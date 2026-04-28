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

from plone import api as ploneapi

from senaite.jsonapi import api
from senaite.jsonapi import logger
from senaite.jsonapi import request as req
from senaite.jsonapi.config import JWT_COOKIE_ID
from senaite.jsonapi.config import JWT_TOKENS_TIMEOUT
from senaite.jsonapi.pas.plugin import create_token
from senaite.jsonapi.pas.plugin import timestamp
from senaite.jsonapi.v1 import add_route
from senaite.jsonapi.interfaces import IInfo
from senaite.jsonapi.interfaces import IUsersFilter
from zope.component import getAdapters


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
        "authenticated": current.getId() == user.getId(),
        "api_url": api.url_for("senaite.jsonapi.v1.users", username=user.getId()),
    }

    for k, v in api.get_user_properties(user).items():
        if api.is_date(v):
            v = api.to_iso_date(v)
        if not api.is_json_serializable(v):
            logger.warn("User property '{}' is not JSON serializable".format(k))
            continue
        info[k] = v

    for name, adapter in getAdapters((pu,), IInfo):
        info.update(adapter.to_dict())

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

    # Allow addons to filter the user list via adapters
    for name, adapter in getAdapters((request,), IUsersFilter):
        if username is None:
            user_ids = adapter.filter(user_ids)

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

    Authenticates the user and issues a JSON Web Token (JWT). Two
    authentication modes are supported:

    1. HTTP Basic auth (header ``Authorization: Basic ...``): no body
       fields are needed; the route just issues a token for the user
       that was already authenticated by the PAS layer.
    2. Form login: POST ``__ac_name`` and ``__ac_password`` as form
       fields. The route logs the user in via the cookie auth plugin
       and then issues the token.

    The JWT is returned in the JSON body as ``token`` (with ``expires``
    as a Unix timestamp) and is also set as the ``token`` HttpOnly
    cookie so subsequent requests can be authenticated either via
    ``Authorization: Bearer <token>`` or via the cookie.
    """
    # extract the data
    __ac_name = request.get("__ac_name", None)
    __ac_password = request.get("__ac_password", None)

    logger.info("*** LOGIN %s ***" % (__ac_name or "<basic>"))

    # Form-based login path: log the user in via the cookie auth plugin.
    # Basic-auth requests (and other PAS-authenticated requests) skip this
    # block since the user is already authenticated by the time the route
    # is dispatched.
    if __ac_name is not None and __ac_password is not None:
        acl_users = api.get_tool("acl_users")
        # XXX hard coded
        acl_users.credentials_cookie_auth.login()

    if api.is_anonymous():
        api.fail(401, "Invalid Credentials")

    # Issue a JWT for the now-authenticated user
    userid = api.get_current_user().getId()
    expires = timestamp(seconds=JWT_TOKENS_TIMEOUT)
    token = create_token(userid, exp=expires)

    # Set the token as an HttpOnly cookie so cookie-based clients can use
    # it transparently
    request.response.setCookie(
        JWT_COOKIE_ID, token,
        http_only=True, path="/", same_site="None", expires=expires,
    )

    # Return the user info merged with the token payload
    info = get(context, request, username=userid) or {}
    info.update({
        "token": token,
        "expires": expires,
    })
    return info


@add_route("/logout", "senaite.jsonapi.v1.logout", methods=["GET"])
@add_route("/users/logout", "senaite.jsonapi.v1.users.logout", methods=["GET"])
def logout(context, request):
    """ Logout Route
    """

    logger.info("*** LOGOUT ***")

    # Avoid redirect after logout
    request.set("HTTP_REFERER", "")

    acl_users = api.get_tool("acl_users")
    acl_users.logout(request)

    # Expire the JWT cookie on the client side. Note this does not
    # invalidate the JWT itself — to revoke a token before its
    # expiration, rotate the user's signing secret with
    # ``senaite.jsonapi.pas.plugin.rotate_secret``.
    request.response.expireCookie(JWT_COOKIE_ID, path="/")

    return {
        "url": api.url_for("senaite.jsonapi.v1.users"),
        "authenticated": False,
        "success": True,
    }
