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

from AccessControl import Unauthorized
from senaite.jsonapi import api
from senaite.jsonapi import logger
from senaite.jsonapi.exceptions import BadRequestError
from senaite.jsonapi.exceptions import ForbiddenError
from senaite.jsonapi.interfaces import IDataManager
from senaite.jsonapi.interfaces import IUpdate
from zope import interface

# Keys consumed by the worksheet assembly instead of the generic
# fieldmanager path. "Analyses" is accepted as an alias of "analyses".
WS_ANALYSES = "analyses"
WS_ANALYSES_ALIAS = "Analyses"
WS_REFERENCE = "reference_analyses"
WS_DUPLICATE = "duplicate_analyses"

# Keys never routed through the data manager on update.
SKIP_FIELDS = ("id", "transition")


def extract_uid(value):
    """Return the UID of a value that is either a UID string or a mapping
    carrying a `uid` key, else None.
    """
    if isinstance(value, dict):
        return value.get("uid")
    if api.is_uid(value):
        return value
    return None


class WorksheetUpdate(object):
    """IUpdate adapter that assembles a Worksheet through its own add
    methods.

    Setting the `analyses` field directly only writes the back reference;
    the worksheet `Layout` (what the results view renders) stays empty.
    This adapter routes routine analyses through `Worksheet.addAnalyses`
    so a slot layout is built, and exposes the QC add methods (reference
    and duplicate analyses) that are otherwise unreachable through the
    API.

    Recognised keys (all optional):

    - `analyses`: list of routine analysis UIDs (or `{"uid": ...}`)
    - `reference_analyses`: list of
      `{"reference_uid": <ReferenceSample>, "services": [<uid>, ...],
        "slot": <int>}`
    - `duplicate_analyses`: list of
      `{"src_slot": <int>, "dest_slot": <int>}`

    Every other key is applied through the regular field managers. The
    caller (`update_object_with_data`) validates, fires any `transition`
    and reindexes after this adapter returns.
    """
    interface.implements(IUpdate)

    def __init__(self, context):
        self.context = context

    def is_update_allowed(self):
        """Worksheets are assembled through this adapter."""
        return True

    def update_object(self, **data):
        """Apply plain fields, then assemble routine and QC analyses."""
        analyses = data.pop(WS_ANALYSES, None)
        if analyses is None:
            analyses = data.pop(WS_ANALYSES_ALIAS, None)
        references = data.pop(WS_REFERENCE, None)
        duplicates = data.pop(WS_DUPLICATE, None)

        self.set_fields(data)
        self.add_analyses(analyses)
        self.add_reference_analyses(references)
        self.add_duplicate_analyses(duplicates)
        return self.context

    def set_fields(self, data):
        """Apply the non-assembly fields through the data manager."""
        dm = IDataManager(self.context)
        for name, value in data.items():
            if name in SKIP_FIELDS:
                continue
            try:
                success = dm.set(name, value, **data)
            except Unauthorized:
                raise ForbiddenError(
                    "Not allowed to set the field '%s'" % name)
            except ValueError as exc:
                raise BadRequestError(str(exc))
            if success is False:
                logger.warn("WorksheetUpdate::skipping key=%r", name)

    def add_analyses(self, analyses):
        """Route routine analyses through Worksheet.addAnalyses."""
        objects = self.resolve_objects(analyses)
        if objects:
            self.context.addAnalyses(objects)

    def add_reference_analyses(self, records):
        """Create QC reference analyses from reference samples."""
        for record in records or []:
            reference = self.get_object(record.get("reference_uid"))
            service_uids = record.get("services") or []
            slot = to_slot(record.get("slot"))
            if reference is None or not service_uids:
                logger.warn(
                    "Skipping reference analyses record %r", record)
                continue
            self.context.addReferenceAnalyses(reference, service_uids, slot)

    def add_duplicate_analyses(self, records):
        """Create QC duplicate analyses from a source slot."""
        for record in records or []:
            src_slot = record.get("src_slot")
            if src_slot is None:
                logger.warn(
                    "Skipping duplicate analyses record %r", record)
                continue
            dest_slot = to_slot(record.get("dest_slot"))
            self.context.addDuplicateAnalyses(to_slot(src_slot), dest_slot)

    def resolve_objects(self, values):
        """Resolve a list of UID/`{uid}` values to objects."""
        if not values:
            return []
        if not isinstance(values, (list, tuple)):
            values = [values]
        objects = []
        for item in values:
            obj = self.get_object(extract_uid(item))
            if obj is None:
                logger.warn("Skipping unresolvable analysis %r", item)
                continue
            objects.append(obj)
        return objects

    def get_object(self, uid):
        if not uid:
            return None
        return api.get_object_by_uid(uid, None)


def to_slot(value):
    """Coerce a slot value to a non-negative int (0 = auto)."""
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
