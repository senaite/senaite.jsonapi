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

"""JSON-compatible serialization of catalog brains and content objects.

Every function here turns a brain/object into a JSON-ready dict (or
list of dicts). The routes use `get_info` as the main entry point;
the four url/parent/children/file/workflow helpers are exposed so
fieldmanagers and add-on serializers can reuse them.

The module imports from `senaite.jsonapi.api` (the package's
`__init__.py`) at module-load time. This is safe because the
re-export line for this module lives at the bottom of `__init__.py`,
after every helper referenced here has already been bound in the
package namespace.
"""

from bika.lims import api as bika_api
from bika.lims.api import snapshot
from AccessControl import Unauthorized
from Products.ATContentTypes.utils import DT2dt
from senaite.jsonapi import logger
from senaite.jsonapi import request as req
from senaite.jsonapi.api import get_brain
from senaite.jsonapi.api import get_contents
from senaite.jsonapi.api import get_endpoint
from senaite.jsonapi.api import get_field
from senaite.jsonapi.api import get_id
from senaite.jsonapi.api import get_object
from senaite.jsonapi.api import get_parent
from senaite.jsonapi.api import get_portal_type
from senaite.jsonapi.api import get_tool
from senaite.jsonapi.api import get_uid
from senaite.jsonapi.api import get_url
from senaite.jsonapi.api import is_brain
from senaite.jsonapi.api import is_relationship_object
from senaite.jsonapi.api import is_root
from senaite.jsonapi.api import portal_type_to_resource
from senaite.jsonapi.api import url_for
from senaite.jsonapi.interfaces import IFieldManager
from senaite.jsonapi.interfaces import IInfo
from zope.component import getAdapters


def get_info(brain_or_object, endpoint=None, complete=False):
    """Extract JSON-ready data from a catalog brain or content object.
    """
    if not is_brain(brain_or_object):
        brain_or_object = get_brain(brain_or_object)
        if brain_or_object is None:
            logger.warn(
                "Couldn't find/fetch brain of {}".format(brain_or_object))
            return {}
        complete = True

    # Relationship objects are internal glue between two content
    # items; they are never a target of the API themselves.
    if is_relationship_object(brain_or_object):
        logger.warn(
            "Skipping relationship object {}".format(repr(brain_or_object)))
        return {}

    # merge IInfo adapters registered for the brain
    info = {}
    for name, adapter in getAdapters((brain_or_object, ), IInfo):
        info.update(adapter.to_dict())

    info.update(get_url_info(brain_or_object, endpoint))
    info.update(get_parent_info(brain_or_object))

    if complete:
        # Wake up the full content object so IInfo adapters and the
        # snapshot version have real attribute access.
        obj = bika_api.get_object(brain_or_object)

        for name, adapter in getAdapters((obj, ), IInfo):
            info.update(adapter.to_dict())

        info["version"] = snapshot.get_version(obj)

        # workflow only when explicitly requested (?complete=yes
        # &workflow=yes)
        if req.get_workflow(False):
            info.update(get_workflow_info(obj))

    return info


def get_url_info(brain_or_object, endpoint=None):
    """URL identifiers for a brain/object: uid, url, api_url."""
    if endpoint is None:
        endpoint = get_endpoint(brain_or_object)

    uid = get_uid(brain_or_object)
    resource = portal_type_to_resource(get_portal_type(brain_or_object))

    return {
        "uid": uid,
        "url": get_url(brain_or_object),
        "api_url": url_for(endpoint, resource=resource, uid=uid),
    }


def get_parent_info(brain_or_object, endpoint=None):
    """URL identifiers for the parent, or {} for the portal root.

    Returns empty parent fields (rather than raising) when the caller
    lacks View on the parent.
    """
    if is_root(brain_or_object):
        return {}

    try:
        parent = get_parent(brain_or_object)
    except Unauthorized:
        return {
            "parent_id": "",
            "parent_uid": "",
            "parent_url": "",
        }

    if endpoint is None:
        endpoint = get_endpoint(parent)

    resource = portal_type_to_resource(get_portal_type(parent))
    parent_uid = get_uid(parent)

    return {
        "parent_id": get_id(parent),
        "parent_uid": parent_uid,
        "parent_url": url_for(endpoint, resource=resource, uid=parent_uid),
    }


def get_children_info(brain_or_object, complete=False):
    """Serialize the contained content items of a folderish object."""
    children = get_contents(brain_or_object)
    items = [get_info(child, complete=complete) for child in children]
    return {
        "children_count": len(items),
        "children": items,
    }


def get_file_info(obj, fieldname, default=None):
    """Serialize a file field. Returns None for an empty field.

    The raw bytes are only included when the request explicitly asks
    for them via `?filedata=yes` (base64-encoded).
    """
    fm = IFieldManager(get_field(obj, fieldname))

    if fm.get_size(obj) == 0:
        return None

    out = {
        "content_type": fm.get_content_type(obj),
        "filename": fm.get_filename(obj),
        "download": fm.get_download_url(obj),
    }
    if req.get_filedata(False):
        out["data"] = fm.get_data(obj).encode("base64")
    return out


def get_workflow_info(brain_or_object, endpoint=None):
    """Serialize every workflow assigned to the object.

    Returns {"workflow_info": [ {workflow, status, review_state,
    transitions, review_history}, ... ]} or an empty list if no
    workflow is assigned.
    """
    obj = get_object(brain_or_object)
    wf_tool = get_tool("portal_workflow")
    workflows = wf_tool.getWorkflowsFor(obj)
    if not workflows:
        return []

    out = []
    for workflow in workflows:
        status_info = wf_tool.getStatusOf(workflow.getId(), obj)
        if status_info is None:
            continue

        state = _current_state(status_info)
        if state is None:
            logger.warn("No state variable found for {} -> {}".format(
                repr(obj), status_info))
            continue

        transitions = [
            _transition_to_dict(t)
            for t in wf_tool.getTransitionsFor(obj)
        ]
        review_history = [
            _review_history_to_dict(rh)
            for rh in workflow.getInfoFor(obj, "review_history", "")
        ]

        out.append({
            "workflow": workflow.getId(),
            "status": workflow.states[state].title,
            "review_state": state,
            "transitions": transitions,
            "review_history": review_history,
        })
    return {"workflow_info": out}


def _current_state(status_info):
    """Return the first non-None state key from a workflow status dict.

    SENAITE workflows use one of several state variable names
    (review_state, inactive_state, cancellation_state,
    worksheetanalysis_review_state) depending on the type of workflow;
    the first one present wins.
    """
    return (status_info.get("review_state")
            or status_info.get("inactive_state")
            or status_info.get("cancellation_state")
            or status_info.get("worksheetanalysis_review_state"))


def _transition_to_dict(transition):
    return {
        "title": transition["title"],
        "value": transition["id"],
        "display": transition["description"],
        "url": transition["url"],
    }


def _review_history_to_dict(review_history):
    review_history["time"] = DT2dt(review_history.get("time")).strftime(
        "%Y-%m-%d %H:%M:%S")
    return review_history
