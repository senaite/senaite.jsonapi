# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.JSONAPI.
#
# SENAITE.JSONAPI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
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
# Copyright 2017-2026 by it's authors.
# Some rights reserved, see README and LICENSE.

"""Create / update / delete helpers for the JSON API.

The three top-level route orchestrators (`create_items`, `update_items`,
`delete_items`) plus the low-level building blocks
(`create_object`, `update_object_with_data`, `deactivate_object`,
`create_analysisrequest`, `find_target_container`, `validate_object`)
and the permission checks (`is_creation_allowed`, `is_update_allowed`).

Backward compatibility: every name is re-exported from
`senaite.jsonapi.api` so route code (`v1/routes/content.action` looks
up `api.create_items` / `api.update_items` / `api.delete_items` via
getattr) keeps working unchanged.
"""

import copy

import transaction
from AccessControl import Unauthorized
from bika.lims import api as bika_api
from bika.lims.utils.analysisrequest import (
    create_analysisrequest as _create_ar,
)

from senaite.jsonapi import logger
from senaite.jsonapi import request as req
from senaite.jsonapi import underscore as u
from senaite.jsonapi.api import convert_physical_paths_to_objects
from senaite.jsonapi.api import do_transition_for
from senaite.jsonapi.api import find_objects
from senaite.jsonapi.api import get_object
from senaite.jsonapi.api import get_object_by_path
from senaite.jsonapi.api import get_object_by_record
from senaite.jsonapi.api import get_object_by_uid
from senaite.jsonapi.api import is_root
from senaite.jsonapi.api import make_items_for
from senaite.jsonapi.api import SKIP_UPDATE_FIELDS
from senaite.jsonapi.exceptions import BadRequestError
from senaite.jsonapi.exceptions import ForbiddenError
from senaite.jsonapi.exceptions import NotFoundError
from senaite.jsonapi.interfaces import ICreate
from senaite.jsonapi.interfaces import IDataManager
from senaite.jsonapi.interfaces import IInfo
from senaite.jsonapi.interfaces import IUpdate
from zope.component import getAdapters
from zope.component import queryAdapter
from zope.deprecation import deprecate


# ---------------------------------------------------------------------------
# Route orchestrators (called by v1/routes/content.action via getattr)
# ---------------------------------------------------------------------------

def create_items(portal_type=None, uid=None, endpoint=None, **kw):
    """Create one or more objects from the request payload.

    Container resolution:

    1. If `uid` is given and non-zero, treat it as the target folder's
       UID.
    2. If `uid` is 0, the portal itself is the target folder.
    3. Otherwise the payload must provide `parent_uid` or `parent_path`
       (handled by `find_target_container`).
    """
    req.disable_csrf_protection()

    container = uid and get_object_by_uid(uid) or None
    records = req.get_request_data()

    results = []
    errors = []
    for record in records:
        if portal_type is None:
            portal_type = record.pop("portal_type", None)

        if container is None:
            container = find_target_container(record)

        if not all([container, portal_type]):
            raise BadRequestError(
                "Please provide a container path/uid and portal_type")

        if not is_creation_allowed(portal_type, container):
            raise ForbiddenError("Creation of '{}' in '{}' is not allowed".format(
                portal_type, bika_api.get_path(container)))

        # Wrap each creation in a savepoint so a failure does not leak
        # the generated ID (SENAITE increments a counter on create).
        sp = transaction.savepoint()
        try:
            obj = create_object(container, portal_type, **record)
            results.append(obj)
        except Exception as e:
            sp.rollback()
            logger.exception("Error while creating object: %s", e)
            errors.append(str(e))

    if not results:
        # Surface the underlying reason(s) -- e.g. missing required
        # fields reported by the object's validation ({"field": "required
        # field"}) -- instead of a generic failure, so the caller sees
        # exactly what to fix.
        detail = "; ".join(filter(None, errors))
        raise BadRequestError(
            "No objects could be created: {}".format(detail)
            if detail else "No objects could be created")

    return make_items_for(results, endpoint=endpoint)


def patch_items(portal_type=None, uid=None, endpoint=None, **kw):
    """PATCH is an alias for update_items."""
    return update_items(
        portal_type=portal_type, uid=uid, endpoint=endpoint, **kw)


def put_items(portal_type=None, uid=None, endpoint=None, **kw):
    """PUT is an alias for update_items."""
    return update_items(
        portal_type=portal_type, uid=uid, endpoint=endpoint, **kw)


def update_items(portal_type=None, uid=None, endpoint=None, **kw):
    """Update one or more objects from the request payload.

    1. If `uid` is given, update that object with the first record in
       the body (later records are ignored).
    2. Otherwise, each record must carry a `uid`, `path`, or
       `parent_path` + `id` so the object can be resolved.
    """
    req.disable_csrf_protection()

    records = req.get_request_data()

    obj = get_object_by_uid(uid)
    if obj:
        record = records[0]
        if not is_update_allowed(obj):
            raise ForbiddenError(
                "Update of {} is not allowed".format(bika_api.get_path(obj)))
        obj = update_object_with_data(obj, record)
        return make_items_for([obj], endpoint=endpoint)

    results = []
    for record in records:
        obj = get_object_by_record(record)
        if obj is None:
            continue
        if not is_update_allowed(obj):
            raise ForbiddenError(
                "Update of {} is not allowed".format(bika_api.get_path(obj)))
        obj = update_object_with_data(obj, record)
        results.append(obj)

    if not results:
        raise BadRequestError("No Objects could be updated")

    return make_items_for(results, endpoint=endpoint)


def delete_items(portal_type=None, uid=None, endpoint=None, **kw):
    """Deactivate one or more objects (SENAITE never hard-deletes).

    1. If `uid` is given, that single object is the target.
    2. Otherwise the payload identifies each target
       (`find_objects` handles it).

    The portal object itself is refused; other roots (setup folders)
    fall through to `deactivate_object`, which prevents them from
    transitioning via workflow guards.
    """
    req.disable_csrf_protection()

    objects = find_objects(uid=uid)

    if filter(lambda o: is_root(o), objects):
        raise BadRequestError("Can not delete the portal object")

    results = []
    for obj in objects:
        deactivate_object(obj)

        info = {}
        for name, adapter in getAdapters((obj,), IInfo):
            info.update(adapter.to_dict())
        results.append(info)

    if not results:
        raise NotFoundError("No Objects could be found")

    return results


# ---------------------------------------------------------------------------
# Low-level building blocks
# ---------------------------------------------------------------------------

def find_target_container(record):
    """Resolve the target container from the record's parent_* keys.

    Reads and pops `parent_uid` or `parent_path` from the record.
    Raises NotFoundError when neither resolves to an object.
    """
    parent_uid = record.pop("parent_uid", None)
    parent_path = record.pop("parent_path", None)

    target = None
    if parent_uid:
        target = get_object_by_uid(parent_uid)
    elif parent_path:
        target = get_object_by_path(parent_path)

    if not target:
        raise NotFoundError("No target container found")

    return target


def create_object(container, portal_type, **data):
    """Create a content object inside the container.

    Handles three paths:

    1. A registered `ICreate` adapter with `is_creation_delegated()`
       True fully takes over.
    2. `AnalysisRequest` gets special handling via
       `create_analysisrequest` because of the interim / partition
       machinery that a plain `bika_api.create` skips.
    3. Everything else: create the minimum viable object and then
       apply the record data via `update_object_with_data` so the
       fieldmanagers handle coercion.
    """
    if "id" in data:
        # SENAITE generates its own ID; drop any client-supplied one.
        supplied_id = data.pop("id")
        logger.warn(
            "Passed in ID '{}' omitted! Senaite LIMS generates a proper "
            "ID for you".format(supplied_id))

    try:
        adapter = queryAdapter(container, ICreate, name=portal_type)
        if adapter and adapter.is_creation_delegated():
            logger.info(
                "Delegating 'create' operation of '{}' in '{}'".format(
                    portal_type, bika_api.get_path(container)))
            return adapter.create_object(**data)

        if portal_type == "AnalysisRequest":
            # For AR, physical paths get resolved here; for other types
            # the fieldmanager handles it.
            data = convert_physical_paths_to_objects(data)
            obj = create_analysisrequest(container, **data)
            data = u.omit(data, "SampleType", "Analyses")
            data["Client"] = container
            return obj

        # Standard creation: minimum viable object + record data below.
        obj = bika_api.create(container, portal_type)
    except Unauthorized:
        raise ForbiddenError("You are not allowed to create this content")

    update_object_with_data(obj, data)
    return obj


def create_analysisrequest(container, **data):
    """Create a minimum-viable AnalysisRequest via the bika helper."""
    container = get_object(container)
    request = req.get_request()
    return _create_ar(container, request, data)


def update_object_with_data(content, record):
    """Update `content` with the fields from `record`.

    Delegates to a registered `IUpdate` adapter if one exists;
    otherwise uses the default `IDataManager` machinery.
    """
    content = get_object(content)

    adapter = queryAdapter(content, IUpdate)
    if adapter:
        logger.info(
            "Delegating 'update' operation of '{}'".format(
                bika_api.get_path(content)))
        adapter.update_object(**record)
    else:
        dm = IDataManager(content)
        if dm is None:
            raise BadRequestError("Update for this object is not allowed")

        purged = copy.deepcopy(record)
        for key in SKIP_UPDATE_FIELDS:
            purged.pop(key, None)

        for k, v in purged.items():
            try:
                success = dm.set(k, v, **record)
            except Unauthorized:
                raise ForbiddenError("Not allowed to set the field '%s'" % k)
            except ValueError as exc:
                raise BadRequestError(str(exc))

            if success is False:
                logger.warning("update_object_with_data::skipping key=%r", k)
                continue
            logger.debug("update_object_with_data::field %r updated", k)

    invalid = bika_api.validate(content)
    if invalid:
        raise BadRequestError(u.to_json(invalid))

    if record.get("transition", None):
        t = record.get("transition")
        logger.debug(">>> Do Transition '%s' for Object %s", t, content.getId())
        do_transition_for(content, t)

    content.reindexObject()
    return content


@deprecate("Use senaite.core.api.validate instead")
def validate_object(brain_or_object, data):
    """Validate the entire object. Deprecated; use bika_api.validate."""
    obj = get_object(brain_or_object)
    return bika_api.validate(obj)


def deactivate_object(brain_or_object):
    """Deactivate the given object (SENAITE's soft-delete).

    Refuses the site root explicitly; other refusals come from the
    workflow guard on `deactivate`.
    """
    obj = get_object(brain_or_object)
    if is_root(obj):
        raise ForbiddenError("Deactivating the Portal is not allowed")
    try:
        do_transition_for(brain_or_object, "deactivate")
    except Unauthorized:
        raise ForbiddenError(
            "Not allowed to deactivate object '%s'" % obj.getId())


# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------

def is_creation_allowed(portal_type, container):
    """True if `portal_type` may be created inside `container`.

    Never allows creation directly in the portal root, the classic
    `bika_setup` folder, or the dexterity `senaite_setup` folder.
    Falls back to the container's own `allowed_content_types` filter,
    then to an optional `ICreate` adapter's opinion.
    """
    if container == bika_api.get_portal():
        return False
    if container == bika_api.get_setup():
        return False
    if container == bika_api.get_senaite_setup():
        return False

    container_info = container.getTypeInfo()
    if container_info.filter_content_types:
        if portal_type not in container_info.allowed_content_types:
            return False

    adapter = queryAdapter(container, ICreate, name=portal_type)
    if adapter:
        return adapter.is_creation_allowed()

    return True


def is_update_allowed(obj):
    """True if `obj` may be updated.

    Same denylist as `is_creation_allowed` (portal, bika_setup,
    senaite_setup), applied to the object's parent, plus an optional
    `IUpdate` adapter's opinion.
    """
    if bika_api.is_portal(obj):
        return False

    parent = bika_api.get_parent(obj)
    if bika_api.is_portal(parent):
        return False
    if parent == bika_api.get_setup():
        return False
    if parent == bika_api.get_senaite_setup():
        return False

    adapter = queryAdapter(obj, IUpdate)
    if adapter:
        return adapter.is_update_allowed()

    return True
