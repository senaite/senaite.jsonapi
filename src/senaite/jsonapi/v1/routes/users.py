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
# Copyright 2017-2020 by it's authors.
# Some rights reserved, see README and LICENSE.

from plone import api as ploneapi

from senaite.jsonapi import api
from senaite.jsonapi import logger
from senaite.jsonapi import request as req
from senaite.jsonapi.v1 import add_route


def get_user_info(user):
    """Get the user information
    """
    user = api.get_user(user)
    current = api.get_current_user()

    if api.is_anonymous():
        return {
            "username": current.getUserName(),
            "authenticated": False,
            "roles": current.getRoles(),
            "api_url": api.url_for("senaite.jsonapi.v1.users", username="current"),
        }

    # nothing to do
    if user is None:
        logger.warn("No user found for {}".format(user))
        return None

    # plone user
    pu = user.getUser()

    info = {
        "username": user.getUserName(),
        "roles": user.getRoles(),
        "groups": pu.getGroups(),
        "authenticated": current == user,
        "api_url": api.url_for("senaite.jsonapi.v1.users", username=user.getId()),
    }

    for k, v in api.get_user_properties(user).items():
        if api.is_date(v):
            v = api.to_iso_date(v)
        if not api.is_json_serializable(v):
            logger.warn("User property '{}' is not JSON serializable".format(k))
            continue
        info[k] = v

    return info


# -----------------------------------------------------------------------------
# API ROUTES
# -----------------------------------------------------------------------------

@add_route("/users", "senaite.jsonapi.v1.users", methods=["GET"])
@add_route("/users/<string:username>", "senaite.jsonapi.v1.users", methods=["GET"])
def get(context, request, username=None):
    """Plone users route
    """
    user_ids = []

    # Don't allow anonymous users to query a user other than themselves
    if api.is_anonymous():
        username = "current"

    # query all users if no username was given
    if username is None:
        user_ids = api.get_member_ids()
    elif username == "current":
        current_user = api.get_current_user()
        user_ids = [current_user.getId()]
    else:
        user_ids = [username]

    # Prepare batch
    size = req.get_batch_size()
    start = req.get_batch_start()
    batch = api.make_batch(user_ids, size, start)

    # get the user info for the user ids in the current batch
    users = map(get_user_info, batch.get_batch())

    return {
        "pagesize": batch.get_pagesize(),
        "next": batch.make_next_url(),
        "previous": batch.make_prev_url(),
        "page": batch.get_pagenumber(),
        "pages": batch.get_numpages(),
        "count": batch.get_sequence_length(),
        "items": users,
    }


@add_route("/auth", "senaite.jsonapi.v1.auth", methods=["GET"])
@add_route("/users/auth", "senaite.jsonapi.v1.users.auth", methods=["GET"])
def auth(context, request):
    """ Basic Authentication
    """

    if ploneapi.user.is_anonymous():
        request.response.setStatus(401)
        request.response.setHeader('WWW-Authenticate',
                                   'basic realm="JSONAPI AUTH"', 1)

    logger.info("*** BASIC AUTHENTICATE ***")
    return {}


@add_route("/login", "senaite.jsonapi.v1.login", methods=["GET", "POST"])
@add_route("/users/login", "senaite.jsonapi.v1.users.login", methods=["GET", "POST"])
def login(context, request):
    """ Login Route

    Login route to authenticate a user against Plone.
    """
    # extract the data
    __ac_name = request.get("__ac_name", None)
    __ac_password = request.get("__ac_password", None)

    logger.info("*** LOGIN %s ***" % __ac_name)

    if __ac_name is None:
        api.fail(400, "__ac_name is missing")
    if __ac_password is None:
        api.fail(400, "__ac_password is missing")

    acl_users = api.get_tool("acl_users")

    # XXX hard coded
    acl_users.credentials_cookie_auth.login()

    # XXX amin user won't be logged in if I use this approach
    # acl_users.login()
    # response = request.response
    # acl_users.updateCredentials(request, response, __ac_name, __ac_password)

    if api.is_anonymous():
        api.fail(401, "Invalid Credentials")

    # return the JSON in the same format like the user route
    return get(context, request, username=__ac_name)


@add_route("/logout", "senaite.jsonapi.v1.logout", methods=["GET"])
@add_route("/users/logout", "senaite.jsonapi.v1.users.logout", methods=["GET"])
def logout(context, request):
    """ Logout Route
    """
    logger.info("*** LOGOUT ***")

    acl_users = api.get_tool("acl_users")
    acl_users.logout(request)

    return {
        "url": api.url_for("senaite.jsonapi.v1.users"),
        "success": True
    }
