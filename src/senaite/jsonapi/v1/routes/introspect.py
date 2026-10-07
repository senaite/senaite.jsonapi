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

from bika.lims import api
from senaite.jsonapi.api import fail
from senaite.jsonapi.v1 import add_route


def get_field_type(field):
    """Return a readable type name for an AT or DX schema field

    :param field: An Archetypes field or a zope.schema field
    :returns: The field type name
    :rtype: str
    """
    # Archetypes fields carry a `type` string, e.g. `string`, `reference`
    at_type = getattr(field, "type", None)
    if isinstance(at_type, str):
        return at_type
    # Dexterity (zope.schema) fields: use the class name, e.g. `TextLine`
    return field.__class__.__name__


def is_field_readonly(field):
    """Check whether a field cannot be written through the API

    :param field: An Archetypes field or a zope.schema field
    :rtype: bool
    """
    # Archetypes uses a mode string (`rw`, `r`, `w`)
    mode = getattr(field, "mode", None)
    if isinstance(mode, str):
        return "w" not in mode
    # Dexterity fields expose a readonly flag
    return bool(getattr(field, "readonly", False))


def get_field_info(name, field):
    """Serialize a single schema field to a JSON compatible mapping

    :param name: The field name
    :param field: An Archetypes field or a zope.schema field
    :rtype: dict
    """
    info = {
        "name": name,
        "type": get_field_type(field),
        "required": bool(getattr(field, "required", False)),
        "readonly": is_field_readonly(field),
    }

    # Reference fields expose the portal types they may point to
    allowed_types = getattr(field, "allowed_types", None)
    if allowed_types:
        info["allowed_types"] = list(allowed_types)

    # Single vs. multi valued (AT uses `multiValued`, DX `multi_valued`)
    multi_valued = getattr(field, "multiValued", None)
    if multi_valued is None:
        multi_valued = getattr(field, "multi_valued", None)
    if multi_valued is not None:
        info["multi_valued"] = bool(multi_valued)

    return info


def get_type_info(fti):
    """Serialize a portal type (FTI) to a JSON compatible mapping

    :param fti: A portal type factory type information object
    :rtype: dict
    """
    return {
        "portal_type": fti.getId(),
        "title": fti.Title(),
        "description": fti.Description(),
        "meta_type": getattr(fti, "content_meta_type", None),
        "global_allow": bool(getattr(fti, "global_allow", False)),
    }


def get_catalog_ids(portal_type):
    """Return the ids of the catalogs that index the given portal type

    :param portal_type: The portal type name
    :rtype: list
    """
    catalogs = api.get_catalogs_for(str(portal_type))
    return sorted([catalog.getId() for catalog in catalogs])


def get_type_detail(fti):
    """Serialize a portal type with the extra detail needed to decide where
    and how to create it: the permission required to add it and the catalogs
    that index it. `global_allow` tells whether the type is addable anywhere
    or only where a container explicitly allows it, in which case the addable
    types of a given container are available via `/types?parent_uid=<uid>`.

    :param fti: A portal type factory type information object
    :rtype: dict
    """
    info = get_type_info(fti)
    info["add_permission"] = getattr(fti, "add_permission", None)
    info["catalogs"] = get_catalog_ids(fti.getId())
    return info


def get_fields_for(portal_type):
    """Return the name to field mapping for a portal type

    Dexterity types (including their behaviors) are resolved directly from
    the type name. Archetypes types have no per-type schema lookup, so the
    schema is taken from an existing instance when one is available.

    :param portal_type: The portal type name
    :rtype: OrderedDict
    """
    # component lookups (IDexterityFTI) require a native str name, but URL
    # traversal yields unicode
    portal_type = str(portal_type)
    # Archetypes types have no per-type schema lookup, so introspect an
    # existing instance when one is available
    if api.is_at_type(portal_type):
        results = api.search({"portal_type": portal_type})
        if results:
            return api.get_fields(results[0])
        return {}
    # Dexterity types (including their behaviors) resolve from the type name
    return api.get_fields(portal_type)


@add_route("/types", "senaite.jsonapi.v1.types", methods=["GET"])
@add_route("/types/<string:portal_type>",
           "senaite.jsonapi.v1.types", methods=["GET"])
def types(context, request, portal_type=None):
    """List the registered portal types, or describe a single one

    Pass `parent_uid` (or `parent_path`) to restrict the listing to the
    types that can be added inside that container.
    """
    portal_types = api.get_tool("portal_types")

    if portal_type:
        fti = portal_types.getTypeInfo(portal_type)
        if fti is None:
            fail(404, "Unknown portal type '{}'".format(portal_type))
        return get_type_detail(fti)

    # optionally restrict to the types addable in a container
    container = None
    parent_uid = request.get("parent_uid")
    parent_path = request.get("parent_path")
    if parent_uid:
        container = api.get_object_by_uid(parent_uid, None)
    elif parent_path:
        container = api.get_object_by_path(parent_path, None)

    if container is not None:
        ftis = container.allowedContentTypes()
    else:
        ftis = portal_types.listTypeInfo()

    items = sorted([get_type_info(t) for t in ftis],
                   key=lambda info: info["portal_type"])
    return {"count": len(items), "items": items}


@add_route("/schema/<string:portal_type>",
           "senaite.jsonapi.v1.schema", methods=["GET"])
def schema(context, request, portal_type=None):
    """Describe the schema fields of a portal type

    Returns each field with its type, whether it is required or read only,
    and, for reference fields, the portal types it may point to.
    """
    portal_types = api.get_tool("portal_types")
    if portal_types.getTypeInfo(portal_type) is None:
        fail(404, "Unknown portal type '{}'".format(portal_type))

    fields = get_fields_for(portal_type)
    items = [get_field_info(name, field) for name, field in fields.items()]
    return {
        "portal_type": portal_type,
        "count": len(items),
        "fields": items,
    }


@add_route("/workflow/<string:uid>",
           "senaite.jsonapi.v1.workflow", methods=["GET"])
def workflow(context, request, uid=None):
    """Return the current workflow state and the available transitions

    This answers "what can I do with this object right now" without having
    to guess transition ids.
    """
    obj = api.get_object_by_uid(uid, None)
    if obj is None:
        fail(404, "No object found for uid '{}'".format(uid))

    wftool = api.get_tool("portal_workflow")
    transitions = [
        {"id": transition["id"], "title": transition["title"]}
        for transition in wftool.getTransitionsFor(obj)
    ]
    return {
        "uid": uid,
        "portal_type": api.get_portal_type(obj),
        "review_state": api.get_review_status(obj),
        "transitions": transitions,
    }
