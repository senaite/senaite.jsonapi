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

from calendar import timegm
from datetime import timedelta

import jwt
from AccessControl import ClassSecurityInfo
from bika.lims import api
from BTrees.OOBTree import OOBTree
from plone.keyring.keyring import GenerateSecret
from Products.PluggableAuthService.interfaces import plugins
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from senaite.core.api import dtime
from senaite.jsonapi import PRODUCT_NAME
from senaite.jsonapi.config import JWT_COOKIE_ID
from senaite.jsonapi.config import JWT_HEADER_ID
from senaite.jsonapi.config import JWT_TOKENS_TIMEOUT
from senaite.jsonapi.config import KEY_STORAGE
from zope.annotation.interfaces import IAnnotations
from zope.interface import implementer

# The id of the plugin
ID = "%s.pas.plugin.JWTAuthenticationPlugin" % PRODUCT_NAME

# Meta type name of the plugin
META_TYPE = "%s: JWT Authentication Plugin" % PRODUCT_NAME


@implementer(plugins.IAuthenticationPlugin, plugins.IExtractionPlugin)
class JWTAuthenticationPlugin(BasePlugin):
    """PAS plugin for authentication with JSON Web tokens (JWT).

    JWT authentication is a stateless, token-based method where the SENAITE
    server issues a signed token to a client after a user logs in. The client
    then stores this token and includes it in subsequent requests to access
    protected resources, allowing the server to verify the user's identity
    without needing to store session data on the server-side.
    """

    id = ID
    title = META_TYPE
    meta_type = META_TYPE
    security = ClassSecurityInfo()

    @security.private
    def extractCredentials(self, request):  # noqa camelCase
        """IExtractionPlugin implementation. Extracts the JSON Web Token (JWT)
        from the request, if any. Returns a dict made of {"token": <token>}
        :param request: the HTTPRequest object to extract credentials from
        :return: a dict with credentials
        """
        token = get_jwt_token(request)
        if not token:
            return {}
        return {"token": token}

    @security.private
    def authenticateCredentials(self, credentials):  # noqa camelCase
        """IAuthenticationPlugin implementation, maps credentials to a User ID.
        If credentials cannot be authenticated, return None
        :param credentials: dict with credentials
        :return: a tuple with the user id and login name or None
        """
        # Ignore credentials that are not from our extractor
        extractor = credentials.get("extractor")
        if extractor != self.getId():
            return None

        token = credentials.get("token")
        if not token:
            return None

        # Peek the payload (no signature check) to learn the userid the
        # token claims to belong to. The unverified userid is only used
        # below as a key into the keystorage; it is never trusted on its
        # own (see peek_userid docstring).
        userid = peek_userid(token)
        if not userid:
            return None

        # Look up the user *before* touching the keystorage. This avoids
        # an anonymous DoS where an attacker sprays tokens with random
        # userids and forces the plugin to create a new signing-secret
        # entry on the portal's OOBTree annotation for each one.
        user = api.get_user(userid)
        if not user:
            return None

        # Verify signature and expiration with that user's existing
        # secret. decode_token returns None if no secret is stored for
        # the user yet (i.e. the user has never logged in via /login).
        payload = decode_token(token, userid)
        if not payload:
            return None

        # Defensive: ensure the verified payload still names the same
        # user as the (now signature-verified) claim.
        if api.to_utf8(payload.get("userid"), default=None) != userid:
            return None

        return userid, userid


def get_jwt_token(request):
    """Extracts the JWT token from the request, in this order of preference:
    Authorization: Bearer header, "token" cookie, X-JWT-Auth-Token header.
    """
    # Read from Authorization header. Zope/PAS may consume the
    # Authorization header from the WSGI environ before our plugin
    # runs (so getHeader("Authorization") returns None), but the raw
    # value is cached on request._auth at request init.
    auth = request._auth or ""  # noqa
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip()

    # Read from cookie
    token = request.cookies.get(JWT_COOKIE_ID)
    if token:
        return token

    # Read from header
    return request.getHeader(JWT_HEADER_ID)


def get_keystorage():
    """Returns the OOBTree where per-user JWT signing secrets are stored,
    creating it lazily on the portal's annotations on first access.
    """
    annotation = IAnnotations(api.get_portal())
    storage = annotation.get(KEY_STORAGE)
    if storage is None:
        annotation[KEY_STORAGE] = OOBTree()
    return annotation[KEY_STORAGE]


def signing_secret(userid):
    """Returns the signing secret for the given userid, generating one
    on first call.
    """
    userid = api.to_utf8(userid, default=None)
    if not userid:
        raise ValueError("Invalid userid: %r" % userid)

    storage = get_keystorage()
    data = storage.get(userid)
    if not data:
        storage[userid] = {
            "key": GenerateSecret(),
            "created": timestamp(),
        }
    return storage[userid]["key"]


def rotate_secret(userid):
    """Discards the signing secret for the given userid, so a new one is
    generated on the next call to `signing_secret`. All previously
    issued tokens for the user are invalidated.
    """
    userid = api.to_utf8(userid, default=None)
    if not userid:
        return
    storage = get_keystorage()
    if userid in storage:
        del storage[userid]


def timestamp(seconds=0, minutes=0, hours=0, days=0):
    """Returns a Unix timestamp from GMT plus the given offset.
    """
    delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
    utc = dtime.datetime.utcnow() + delta
    return timegm(utc.utctimetuple())


def peek_userid(token):
    """Returns the `userid` claim of the given token without verifying
    the signature, or None if the token cannot be decoded.

    Decoding the token without verifying its signature is safe in this
    context: the returned `userid` is only used to look up *that
    user's* signing secret, which is then used to verify the signature
    in `decode_token`. A forged token that claims to belong to user
    X but was signed with anything other than X's real secret fails
    signature verification and is rejected. The unverified `userid`
    is never trusted on its own.
    """
    token = api.to_utf8(token, default=None)
    if not token:
        return None
    try:
        # Disable signature verification at peek time, but still
        # require HS256 as the algorithm so a forged "alg": "none"
        # token cannot reach signature verification with no secret.
        # The `verify=False` kwarg was removed in PyJWT 2.x; the
        # `options` form is supported by both 1.x and 2.x.
        payload = jwt.decode(
            token, options={"verify_signature": False},
            algorithms=["HS256"],
        )
    except (ValueError, TypeError, jwt.InvalidTokenError):
        return None
    return api.to_utf8(payload.get("userid"), default=None)


def get_signing_secret(userid):
    """Returns the existing signing secret for `userid` or None.

    Unlike `signing_secret`, this never creates a new secret entry,
    so it is safe to call with an unverified userid claim (e.g. during
    token verification).
    """
    userid = api.to_utf8(userid, default=None)
    if not userid:
        return None
    data = get_keystorage().get(userid)
    if not data:
        return None
    return data.get("key")


def decode_token(token, userid):
    """Decodes the given JWT, verifies the signature with `userid`'s
    secret and checks the expiration. Returns the payload or None.

    Returns None if no signing secret exists for `userid` yet; the
    keystorage entry is only created by `create_token` (called from
    `/login`), never by the verification path. This prevents an
    anonymous attacker from forcing the portal to create one
    keystorage entry per token claim.
    """
    token = api.to_utf8(token, default=None)
    if not token:
        return None
    secret = get_signing_secret(userid)
    if not secret:
        return None
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except (ValueError, TypeError, jwt.InvalidTokenError):
        return None


def create_token(userid, timeout=JWT_TOKENS_TIMEOUT, **kwargs):
    """Creates a JSON Web Token (JWT) for the given userid.
    """
    payload = {
        "userid": userid,
        "exp": timestamp(seconds=timeout),
    }
    payload.update(kwargs)

    secret = signing_secret(userid)
    token = jwt.encode(payload, secret, algorithm="HS256")
    return api.safe_unicode(token)
