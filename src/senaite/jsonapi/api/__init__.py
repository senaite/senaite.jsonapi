# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.JSONAPI.
#
# SENAITE.JSONAPI is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2017-2025 by it's authors.
# Some rights reserved, see README and LICENSE.

import datetime
import json

from Acquisition import ImplicitAcquisitionWrapper
from bika.lims import api
from DateTime import DateTime
from plone import api as ploneapi
from plone.behavior.interfaces import IBehaviorAssignable
from plone.jsonapi.core import router
from Products.CMFPlone.PloneBatch import Batch
from Products.ZCatalog.Lazy import LazyMap
from senaite.core.api import dtime
from senaite.jsonapi import logger
from senaite.jsonapi import request as req
from senaite.jsonapi import underscore as u
from senaite.jsonapi.exceptions import APIError
from senaite.jsonapi.interfaces import IBatch
from senaite.jsonapi.interfaces import ICatalog
from senaite.jsonapi.interfaces import ICatalogQuery
from senaite.jsonapi.interfaces import IDataManager
from zope.component import getMultiAdapter
from zope.component import queryAdapter
from zope.schema import getFields

_marker = object()

DEFAULT_ENDPOINT = "senaite.jsonapi.v1.get"

SKIP_UPDATE_FIELDS = ["id", ]


# -----------------------------------------------------------------------------
#   JSON API (CRUD) Functions (called by the route providers)
# -----------------------------------------------------------------------------

# GET RECORD
def get_record(uid=None):
    """Get a single record
    """
    obj = None
    if uid is not None:
        obj = get_object_by_uid(uid)
    else:
        obj = get_object_by_request()
    if obj is None:
        fail(404, "No object found")
    complete = req.get_complete(default=_marker)
    if complete is _marker:
        complete = True
    items = make_items_for([obj], complete=complete)
    return u.first(items)


# GET BATCHED
def get_batched(portal_type=None, uid=None, endpoint=None, **kw):
    """Get batched results
    """

    # fetch the catalog results
    results = get_search_results(portal_type=portal_type, uid=uid, **kw)

    # fetch the batch params from the request
    size = req.get_batch_size()
    start = req.get_batch_start()

    # check for existing complete flag
    complete = req.get_complete(default=_marker)
    if complete is _marker:
        # if the uid is given, get the complete information set
        complete = uid and True or False

    # return a batched record
    return get_batch(results, size, start, endpoint=endpoint,
                     complete=complete)


# Route orchestrators (create_items, patch_items, put_items,
# update_items, delete_items) live in senaite.jsonapi.api.mutation and
# are re-exported at the bottom of this module.


def make_items_for(brains_or_objects, endpoint=None, complete=False):
    """Generate API compatible data items for the given list of brains/objects

    :param brains_or_objects: List of objects or brains
    :type brains_or_objects: list/Products.ZCatalog.Lazy.LazyMap
    :param endpoint: The named URL endpoint for the root of the items
    :type endpoint: str/unicode
    :param complete: Flag to wake up the object and fetch all data
    :type complete: bool
    :returns: A list of extracted data items
    :rtype: list
    """

    # check if the user wants to include children
    include_children = req.get_children(False)

    # optional field projection: ?fields=uid,id,title,...
    # empty set means no projection (full object returned)
    fields = req.get_fields()

    def extract_data(brain_or_object):
        info = get_info(brain_or_object, endpoint=endpoint, complete=complete)
        if include_children and is_folderish(brain_or_object):
            info.update(get_children_info(brain_or_object, complete=complete))
        if fields:
            info = {k: info[k] for k in fields if k in info}
        return info

    return map(extract_data, brains_or_objects)


# Serialization helpers (get_info, get_url_info, get_parent_info,
# get_children_info, get_file_info, get_workflow_info) live in
# senaite.jsonapi.api.serialization and are re-exported at the bottom
# of this module.


# -----------------------------------------------------------------------------
#   API
# -----------------------------------------------------------------------------

def fail(status, msg):
    """Raise an APIError with the given HTTP status and message.

    Kept as a thin helper for legacy call sites. New code should raise
    a specific typed subclass (NotFoundError, UnauthorizedError,
    ForbiddenError, BadRequestError, ConflictError, ValidationError)
    from senaite.jsonapi.exceptions so the response envelope carries
    a meaningful `type` field.
    """
    if msg is None:
        msg = "Reason not given."
    raise APIError("{}".format(msg), status=status)


def check_permission(permission, context=None):
    """Check the given permission on context (portal root if None).

    Raises UnauthorizedError for anonymous callers, ForbiddenError for
    authenticated callers that lack the permission. Returns None on
    success.
    """
    from senaite.jsonapi.exceptions import ForbiddenError
    from senaite.jsonapi.exceptions import UnauthorizedError

    if context is None:
        context = get_portal()
    if ploneapi.user.has_permission(permission, obj=context):
        return
    if is_anonymous():
        raise UnauthorizedError("Authentication required")
    raise ForbiddenError("You do not have permission to access this resource")


def search(portal_type=None, **kw):
    """Search the catalog adapter

    :returns: Catalog search results
    :rtype: iterable
    """
    portal = get_portal()
    if portal_type is None:
        # try to get it over the request
        portal_type = req.get("portal_type", None)
    catalog = getMultiAdapter((portal, portal_type), interface=ICatalog)
    catalog_query = ICatalogQuery(catalog)
    query = catalog_query.make_query(**kw)
    return catalog(query)


def get_search_results(portal_type=None, uid=None, **kw):
    """Search the catalog and return the results

    :returns: Catalog search results
    :rtype: iterable
    """

    # If we have an UID, return the object immediately
    if uid is not None:
        logger.info("UID '%s' found, returning the object immediately" % uid)
        return u.to_list(get_object_by_uid(uid))

    # allow to search search for the Plone Site with portal_type
    include_portal = False
    if u.to_string(portal_type) == "Plone Site":
        include_portal = True

    # The request may contain a list of portal_types, e.g.
    # `?portal_type=Document&portal_type=Plone Site`
    if "Plone Site" in u.to_list(req.get("portal_type")):
        include_portal = True

    # Build and execute a catalog query
    results = search(portal_type=portal_type, uid=uid, **kw)

    if include_portal:
        results = list(results) + u.to_list(get_portal())

    return results


def get_portal():
    """Proxy to senaite.api.get_portal
    """
    return api.get_portal()


def get_tool(name, default=_marker):
    """Proxy to senaite.api.get_tool
    """
    return api.get_tool(name, default=default)


def get_object(brain_or_object):
    """Proxy to senaite.api.get_object
    """
    return api.get_object(brain_or_object)


def get_brain(brain_or_object):
    """Return a ZCatalog brain for the object

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: True if the object is a catalog brain
    :rtype: bool
    """
    if is_brain(brain_or_object):
        return brain_or_object
    if is_root(brain_or_object):
        return brain_or_object

    # fetch the brain by UID
    uid = get_uid(brain_or_object)
    portal_type = api.get_portal_type(brain_or_object)
    query = {"UID": uid, "portal_type": portal_type}
    results = api.search(query)
    if len(results) == 0:
        return None
    if len(results) > 1:
        fail(500, "More than one object with UID={}".format(uid))
    return results[0]


def is_brain(brain_or_object):
    """Proxy to senaite.api.is_brain
    """
    return api.is_brain(brain_or_object)


def is_at_content(brain_or_object):
    """Proxy to senaite.api.is_at_content
    """
    return api.is_at_content(brain_or_object)


def is_dexterity_content(brain_or_object):
    """Proxy to senaite.api.is_dexterity_content
    """
    return api.is_dexterity_content(brain_or_object)


def get_schema(brain_or_object):
    """Get the schema of the content

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: Schema object
    """
    obj = get_object(brain_or_object)
    if is_root(obj):
        return None
    if is_dexterity_content(obj):
        pt = get_tool("portal_types")
        fti = pt.getTypeInfo(obj.portal_type)
        return fti.lookupSchema()
    if is_at_content(obj):
        return obj.Schema()
    fail(400, "{} has no Schema.".format(repr(brain_or_object)))


def get_fields(brain_or_object):
    """Get the list of fields from the object

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: List of fields
    :rtype: list
    """
    obj = get_object(brain_or_object)
    # The portal object has no schema
    if is_root(obj):
        return {}
    # rely on core's api
    return api.get_fields(obj)


def get_field(brain_or_object, name, default=None):
    """Return the named field
    """
    fields = get_fields(brain_or_object)
    return fields.get(name, default)


def get_behaviors(brain_or_object):
    """Iterate over all behaviors that are assigned to the object

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: Behaviors
    :rtype: list
    """
    obj = get_object(brain_or_object)
    if not is_dexterity_content(obj):
        fail(400, "Only Dexterity contents can have assigned behaviors")
    assignable = IBehaviorAssignable(obj, None)
    if not assignable:
        return {}
    out = {}
    for behavior in assignable.enumerateBehaviors():
        for name, field in getFields(behavior.interface).items():
            out[name] = field
    return out


def is_root(brain_or_object):
    """Proxy to senaite.api.is_portal
    """
    return api.is_portal(brain_or_object)


def is_folderish(brain_or_object):
    """Proxy to senaite.api.is_folderish
    """
    return api.is_folderish(brain_or_object)


def is_uid(uid):
    """Checks if the passed in uid is a valid UID

    :param uid: The uid to check
    :type uid: string
    :return: True if the uid is a valid 32 alphanumeric uid or '0'
    :rtype: bool
    """
    if not isinstance(uid, basestring):
        return False
    if uid != "0" and len(uid) != 32:
        return False
    return True


def is_path(path):
    """Checks if the passed in path is a valid Path within the portal

    :param path: The path to check
    :type uid: string
    :return: True if the path is a valid path within the portal
    :rtype: bool
    """
    if not isinstance(path, basestring):
        return False
    portal_path = get_path(get_portal())
    if not path.startswith(portal_path):
        return False
    obj = get_object_by_path(path)
    if obj is None:
        return False
    return True


def calculate_delta_date(literal):
    """Calculate the date in the past from the given literal
    :param literal: A date literal, e.g. "today"
    :type literal: str
    :returns: Date between the literal and today
    :rtype: DateTime
    """
    mapping = {
        "today": 0,
        "yesterday": 1,
        "this-week": 7,
        "this-month": 30,
        "this-year": 365,
    }
    today = DateTime(DateTime().Date())  # current date without the time
    return today - mapping.get(literal, 0)


def calculate_since_date(since):
    """Calculates the "since" date

    Returns the DateTime representing the value passed in. If the value is a
    duration of time (either an str in `ymd` format or a relativedelta), it
    calculates the since date using current date time as the end date.

    :param since: A date/datetime-like format or a time interval as ymd format
    :type since: date/datetime/str/relativedelta
    :returns: Date when the event started back the period in ymd format
    :rtype: DateTime
    """
    since_dt = dtime.to_DT(since)
    if since_dt:
        return since_dt

    since_dt = dtime.get_since_date(since)
    return dtime.to_DT(since_dt)


def is_json_serializable(thing):
    """Checks if the given thing can be serialized to JSON

    :param thing: The object to check if it can be serialized
    :type thing: arbitrary object
    :returns: True if it can be JSON serialized
    :rtype: bool
    """
    try:
        json.dumps(thing)
        return True
    except TypeError:
        return False


def to_json_value(obj, fieldname, value=_marker, default=None):
    """JSON save value encoding

    :param obj: Content object
    :type obj: ATContentType/DexterityContentType
    :param fieldname: Schema name of the field
    :type fieldname: str/unicode
    :param value: The field value
    :type value: depends on the field type
    :returns: JSON encoded field value
    :rtype: field dependent
    """

    # This function bridges the value of the field to a probably more complex
    # JSON structure to return to the client.

    # extract the value from the object if omitted
    if value is _marker:
        value = IDataManager(obj).json_data(fieldname)

    # convert objects
    if isinstance(value, ImplicitAcquisitionWrapper):
        return get_url_info(value)

    # check if the value is callable
    if callable(value):
        value = value()

    # convert dates
    if is_date(value):
        return to_iso_date(value)

    # check if the value is JSON serializable
    if not is_json_serializable(value):
        logger.warn("Output {} is not JSON serializable".format(repr(value)))
        return default

    return value


def is_date(thing):
    """Checks if the given thing represents a date

    :param thing: The object to check if it is a date
    :type thing: arbitrary object
    :returns: True if we have a date object
    :rtype: bool
    """
    # known date types
    date_types = (datetime.datetime,
                  datetime.date,
                  DateTime)
    return isinstance(thing, date_types)


def is_lazy_map(thing):
    """Checks if the passed in thing is a LazyMap

    :param thing: The thing to test
    :type thing: any
    :returns: True if the thing is a richtext value
    :rtype: bool
    """
    return isinstance(thing, LazyMap)


def to_iso_date(date, default=None):
    """ISO representation for the date object

    :param date: A date object
    :type field: datetime/DateTime
    :returns: The ISO format of the date
    :rtype: str
    """

    # not a date
    if not is_date(date):
        return default

    # handle Zope DateTime objects
    if isinstance(date, (DateTime)):
        return date.ISO8601()

    # handle python datetime objects
    return date.isoformat()


def get_contents(brain_or_object):
    """Lookup folder contents for this object.

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: List of contained contents
    :rtype: list/Products.ZCatalog.Lazy.LazyMap
    """

    # Nothing to do if the object is contentish
    if not is_folderish(brain_or_object):
        return []

    # Returning objects (not brains) to make sure we do not miss any child.
    # It may happen when children belong to different catalogs and not
    # found on 'portal_catalog'.
    ret = filter(lambda obj: api.is_object(obj),
                 api.get_object(brain_or_object).objectValues())
    return ret


def get_parent(brain_or_object):
    """Locate the parent object of the content/catalog brain

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: parent object
    :rtype: Parent content
    """

    if is_root(brain_or_object):
        return get_portal()

    if is_brain(brain_or_object):
        parent_path = get_parent_path(brain_or_object)
        return get_object_by_path(parent_path)

    return brain_or_object.aq_parent


def get_object_by_uid(uid, default=None):
    """Proxy to senaite.api.get_object_by_uid
    """
    return api.get_object_by_uid(uid, default)


def get_path(brain_or_object):
    """Proxy to senaite.api.get_path
    """
    return api.get_path(brain_or_object)


def get_parent_path(brain_or_object):
    """Proxy to senaite.api.get_parent_path
    """
    return api.get_parent_path(brain_or_object)


def get_id(brain_or_object):
    """Proxy to senaite.api.get_id
    """
    return api.get_id(brain_or_object)


def get_uid(brain_or_object):
    """Proxy to senaite.api.get_uid
    """
    return api.get_uid(brain_or_object)


def get_url(brain_or_object):
    """Proxy to senaite.api.get_url
    """
    return api.get_url(brain_or_object)


def get_portal_type(brain_or_object):
    """Proxy to senaite.api.get_portal_type
    """
    return api.get_portal_type(brain_or_object)


def do_transition_for(brain_or_object, transition):
    """Proxy to senaite.api.do_transition_for
    """
    return api.do_transition_for(brain_or_object, transition)


def get_portal_types():
    """Get a list of all portal types

    :retruns: List of portal type names
    :rtype: list
    """
    types_tool = get_tool("portal_types")
    return types_tool.listContentTypes()


def get_resource_mapping():
    """Map resources used in the routes to portal types

    :returns: Mapping of resource->portal_type
    :rtype: dict
    """
    portal_types = get_portal_types()
    resources = map(portal_type_to_resource, portal_types)
    return dict(zip(resources, portal_types))


def portal_type_to_resource(portal_type):
    """Converts a portal type name to a resource name

    :param portal_type: Portal type name
    :type name: string
    :returns: Resource name as it is used in the content route
    :rtype: string
    """
    resource = portal_type.lower()
    resource = resource.replace(" ", "")
    return resource


def resource_to_portal_type(resource):
    """Converts a resource to a portal type

    :param resource: Resource name as it is used in the content route
    :type name: string
    :returns: Portal type name
    :rtype: string
    """
    if resource is None:
        return None

    resource_mapping = get_resource_mapping()
    portal_type = resource_mapping.get(resource.lower())

    if portal_type is None:
        logger.warn("Could not map the resource '{}' "
                    "to any known portal type".format(resource))

    return portal_type


# is_creation_allowed and is_update_allowed live in
# senaite.jsonapi.api.mutation and are re-exported at the bottom of
# this module.


def url_for(endpoint, default=DEFAULT_ENDPOINT, **values):
    """Looks up the API URL for the given endpoint

    :param endpoint: The name of the registered route (aka endpoint)
    :type endpoint: string
    :returns: External URL for this endpoint
    :rtype: string/None
    """

    try:
        return router.url_for(endpoint, force_external=True, values=values)
    except Exception:
        logger.warn("Could not build API URL for endpoint '%s'. "
                    "No route provider registered?" % endpoint)
        # build generic API URL
        return router.url_for(default, force_external=True, values=values)


def get_endpoint(brain_or_object, default=DEFAULT_ENDPOINT):
    """Calculate the endpoint for this object

    :param brain_or_object: A single catalog brain or content object
    :type brain_or_object: ATContentType/DexterityContentType/CatalogBrain
    :returns: Endpoint for this object
    :rtype: string
    """
    portal_type = get_portal_type(brain_or_object)
    resource = portal_type_to_resource(portal_type)

    # Try to get the right namespaced endpoint
    endpoints = router.DefaultRouter.view_functions.keys()
    if resource in endpoints:
        return resource  # exact match
    endpoint_candidates = filter(lambda e: e.endswith(resource), endpoints)
    if len(endpoint_candidates) == 1:
        # only return the namespaced endpoint, if we have an exact match
        return endpoint_candidates[0]

    return default


def get_object_by_request():
    """Find an object by request parameters

    Inspects request parameters to locate an object

    :returns: Found Object or None
    :rtype: object
    """
    data = req.get_form() or req.get_query_string()
    return get_object_by_record(data)


def get_object_by_record(record):
    """Find an object by a given record

    Inspects request the record to locate an object

    :param record: A dictionary representation of an object
    :type record: dict
    :returns: Found Object or None
    :rtype: object
    """

    # nothing to do here
    if not record:
        return None

    if record.get("uid"):
        return get_object_by_uid(record["uid"])
    if record.get("path"):
        return get_object_by_path(record["path"])
    if record.get("parent_path") and record.get("id"):
        path = "/".join([record["parent_path"], record["id"]])
        return get_object_by_path(path)

    logger.warn("get_object_by_record::No object found! record='%r'" % record)
    return None


def get_object_by_path(path):
    """Find an object by a given physical path

    :param path: The physical path of the object to find
    :type path: string
    :returns: Found Object or None
    :rtype: object
    """

    # nothing to do here
    if not isinstance(path, basestring):
        return None

    # path must be a string
    path = str(path)

    portal = get_portal()
    portal_path = get_path(portal)

    if path == portal_path:
        return portal

    if path.startswith(portal_path):
        segments = path.split("/")
        path = "/".join(segments[2:])

    try:
        return portal.restrictedTraverse(str(path))
    except (KeyError, AttributeError):
        fail(404, "No object could be found at {}".format(str(path)))


def convert_physical_paths_to_objects(record):
    """Convert all physical paths in the record to objects

    :param record: The record dictionary to convert
    :returns: The record with all physical paths converted to objects
    """
    # Convert all physical paths to objects
    for key, value in record.items():
        if is_path(value):
            record[key] = get_object_by_path(value)
    return record


# User helpers live in senaite.jsonapi.api.users and are re-exported at
# the bottom of this module so they remain importable as
# senaite.jsonapi.api.is_anonymous / get_current_user / ...


def find_objects(uid=None):
    """Find the object by its UID

    1. get the object from the given uid
    2. fetch objects specified in the request parameters
    3. fetch objects located in the request body

    :param uid: The UID of the object to find
    :type uid: string
    :returns: List of found objects
    :rtype: list
    """
    # The objects to cut
    objects = []

    # get the object by the given uid or try to find it by the request
    # parameters
    obj = get_object_by_uid(uid) or get_object_by_request()

    if obj:
        objects.append(obj)
    else:
        # no uid -> go through the record items
        records = req.get_request_data()
        for record in records:
            # try to get the object by the given record
            obj = get_object_by_record(record)

            # no object found for this record
            if obj is None:
                continue
            objects.append(obj)

    return objects


# find_target_container, create_object, create_analysisrequest,
# update_object_with_data, validate_object and deactivate_object live
# in senaite.jsonapi.api.mutation and are re-exported at the bottom.


def is_relationship_object(brain_or_object):
    """Checks if the passed in brain or object is a relationship object

    :param brain_or_object: A single catalog brain or content object
    :return: True if the object is a relationship object
    """
    if 'at_references' in get_path(brain_or_object):
        return True
    return False


# -----------------------------------------------------------------------------
#   Batching Helpers
# -----------------------------------------------------------------------------


def get_batch(sequence, size, start=0, endpoint=None, complete=False):
    """ create a batched result record out of a sequence (catalog brains)
    """

    batch = make_batch(sequence, size, start)

    return {
        "pagesize": batch.get_pagesize(),
        "next": batch.make_next_url(),
        "previous": batch.make_prev_url(),
        "page": batch.get_pagenumber(),
        "pages": batch.get_numpages(),
        "count": batch.get_sequence_length(),
        "items": make_items_for([b for b in batch.get_batch()],
                                endpoint, complete=complete),
    }


def make_batch(sequence, size=25, start=0):
    """Make a batch of the given size from the sequence
    """
    # we call an adapter here to allow backwards compatibility hooks
    return IBatch(Batch(sequence, size, start))


# Backward-compat re-exports. Kept at the bottom so any name the
# extracted module needs from this package (e.g. helpers defined above)
# is already bound at import time. Do not move these to the top.
from senaite.jsonapi.api.users import is_anonymous  # noqa: E402,F401
from senaite.jsonapi.api.users import get_current_user  # noqa: E402,F401
from senaite.jsonapi.api.users import get_member_ids  # noqa: E402,F401
from senaite.jsonapi.api.users import get_user  # noqa: E402,F401
from senaite.jsonapi.api.users import get_user_properties  # noqa: E402,F401
from senaite.jsonapi.api.settings import CONTROLPANEL_INTERFACE_MAPPING  # noqa: E402,F401
from senaite.jsonapi.api.settings import get_registry_records_by_keyword  # noqa: E402,F401
from senaite.jsonapi.api.settings import get_settings_by_keyword  # noqa: E402,F401
from senaite.jsonapi.api.settings import get_settings_from_interface  # noqa: E402,F401
from senaite.jsonapi.api.serialization import get_info  # noqa: E402,F401
from senaite.jsonapi.api.serialization import get_url_info  # noqa: E402,F401
from senaite.jsonapi.api.serialization import get_parent_info  # noqa: E402,F401
from senaite.jsonapi.api.serialization import get_children_info  # noqa: E402,F401
from senaite.jsonapi.api.serialization import get_file_info  # noqa: E402,F401
from senaite.jsonapi.api.serialization import get_workflow_info  # noqa: E402,F401
from senaite.jsonapi.api.mutation import create_items  # noqa: E402,F401
from senaite.jsonapi.api.mutation import patch_items  # noqa: E402,F401
from senaite.jsonapi.api.mutation import put_items  # noqa: E402,F401
from senaite.jsonapi.api.mutation import update_items  # noqa: E402,F401
from senaite.jsonapi.api.mutation import delete_items  # noqa: E402,F401
from senaite.jsonapi.api.mutation import find_target_container  # noqa: E402,F401
from senaite.jsonapi.api.mutation import create_object  # noqa: E402,F401
from senaite.jsonapi.api.mutation import create_analysisrequest  # noqa: E402,F401
from senaite.jsonapi.api.mutation import update_object_with_data  # noqa: E402,F401
from senaite.jsonapi.api.mutation import validate_object  # noqa: E402,F401
from senaite.jsonapi.api.mutation import deactivate_object  # noqa: E402,F401
from senaite.jsonapi.api.mutation import is_creation_allowed  # noqa: E402,F401
from senaite.jsonapi.api.mutation import is_update_allowed  # noqa: E402,F401
