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

from senaite.jsonapi import api
from senaite.jsonapi.v1 import add_route
from senaite.jsonapi.exceptions import BadRequestError
from senaite.jsonapi.exceptions import NotFoundError

ACTIONS = "create,update,delete"

# Map REST HTTP verbs to the corresponding API action for object-addressed
# routes that carry no explicit action segment. GET is served by the
# separate `get` route; POST keeps its historic behaviour (action segment
# or X-HTTP-Method-Override header).
VERB_ACTIONS = {
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


# /<resource (portal_type)>
@add_route("/<string:resource>",
           "senaite.jsonapi.v1.get", methods=["GET"])
#
# /<resource (portal_type)>/<uid>
@add_route("/<string:resource>/<string(length=32):uid>",
           "senaite.jsonapi.v1.get", methods=["GET"])
@add_route("/<string:resource>/<string(length=32):uid>",
           "senaite.jsonapi.v1.get", methods=["GET"])
@add_route("/<string(length=32):uid>",
           "senaite.jsonapi.v1.get", methods=["GET"])
def get(context, request, resource=None, uid=None):
    """GET
    """

    # We have a UID, return the record
    if uid and not resource:
        return api.get_record(uid)

    # we have a UID as resource, return the record
    if api.is_uid(resource):
        return api.get_record(resource)

    portal_type = api.resource_to_portal_type(resource)
    if portal_type is None:
        raise NotFoundError("Not Found")

    return api.get_batched(portal_type=portal_type, uid=uid, endpoint="senaite.jsonapi.v1.get")


# http://werkzeug.pocoo.org/docs/0.11/routing/#builtin-converters
# http://werkzeug.pocoo.org/docs/0.11/routing/#custom-converters
# Object-addressed routes accept the REST verbs (PUT/PATCH -> update,
# DELETE -> delete) in addition to POST. Collection/action-segment
# routes stay POST-only.
@add_route("/<any(" + ACTIONS + "):action>",
           "senaite.jsonapi.v1.action", methods=["POST"])
@add_route("/<string:resource>/<string(length=32):uid>",
           "senaite.jsonapi.v1.action",
           methods=["POST", "PUT", "PATCH", "DELETE"])
@add_route("/<any(" + ACTIONS + "):action>/<string(length=32):uid>",
           "senaite.jsonapi.v1.action", methods=["POST"])
@add_route("/<string(length=32):uid>",
           "senaite.jsonapi.v1.action",
           methods=["POST", "PUT", "PATCH", "DELETE"])
@add_route("/<string:resource>/<any(" + ACTIONS + "):action>",
           "senaite.jsonapi.v1.action", methods=["POST"])
@add_route("/<string:resource>/<any(" + ACTIONS + "):action>/<string(length=32):uid>",
           "senaite.jsonapi.v1.action", methods=["POST"])
def action(context, request, action=None, resource=None, uid=None):
    """Dispatch a create/update/delete action.

    The action is resolved in this order:

    1. Explicit action segment in the URL (e.g. `/{resource}/update/{uid}`).
    2. The HTTP method, for REST-style calls without an action segment:
       PUT and PATCH map to `update`, DELETE maps to `delete`.
    3. The `X-HTTP-Method-Override` header (Backbone.js style), for
       clients that can only send POST.

    A POST without any of these remains an error, as before.
    """
    # 2. Derive the action from the REST verb when no explicit segment
    # was given.
    if action is None:
        method = request.get("REQUEST_METHOD", "POST").upper()
        action = VERB_ACTIONS.get(method)

    # 3. Fall back to the method-override header (Backbone.js REST API).
    if action is None:
        override = request.get_header("HTTP_X_HTTP_METHOD_OVERRIDE", None)
        action = override and override.lower() or None

    # Fetch and call the action function of the API
    func_name = "{}_items".format(action)
    action_func = getattr(api, func_name, None)
    if action_func is None:
        raise BadRequestError(
            "API has no member named '{}'".format(func_name))

    portal_type = api.resource_to_portal_type(resource)
    items = action_func(portal_type=portal_type, uid=uid)

    return {
        "count": len(items),
        "items": items,
        "url": api.url_for("senaite.jsonapi.v1.action", action=action),
    }


@add_route("/search",
           "senaite.jsonapi.v1.search", methods=["GET"])
def search(context, request):
    """Generic search add_route

    <Plonesite>/@@API/v2/search -> returns all contents of the portal
    <Plonesite>/@@API/v2/search?portal_type=Folder -> returns only folders
    ...
    """
    return api.get_batched()
