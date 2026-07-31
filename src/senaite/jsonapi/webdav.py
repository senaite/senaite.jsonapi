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

"""Let the JSON API receive PUT / PATCH / DELETE.

Zope decides very early in publishing -- in `BaseRequest.traverse`,
before the API view is reached -- whether a non-GET/POST request is a
WebDAV client, by reading `request.maybe_webdav_client` (default 1;
only cleared for XML-RPC). When set, ZPublisher may substitute a WebDAV
`NullResource` at path exhaustion, so PUT/PATCH/DELETE can be diverted
away from the API view depending on the traversed view's shape and the
Zope version.

The flag is consumed before traversal, so it cannot be cleared from the
route. The only hook that runs early enough is an `IPubStart`
subscriber. We clear the flag for requests addressed to the JSON API
view so the verb routing added to `v1/routes/content` reaches the view
reliably, instead of relying on the NullResource conditions happening
not to be met.

This is deliberately self-contained in senaite.jsonapi so PUT/PATCH/
DELETE work on the released plone.jsonapi.core (which has no such
bypass). It mirrors the technique used by plone.rest; if a future
plone.jsonapi.core ships an equivalent subscriber, clearing the flag
twice is idempotent.
"""

import logging

logger = logging.getLogger("senaite.jsonapi.webdav")

# Verbs ZPublisher would otherwise hand to the WebDAV machinery instead
# of the API view.
WEBDAV_VERBS = frozenset(["PUT", "PATCH", "DELETE"])

# Path segments that identify a request bound for the JSON API view. The
# plone.jsonapi.core view is registered as @@API and reachable either
# explicitly (@@API) or via acquisition (API).
API_SEGMENTS = frozenset(["@@API", "API"])


def is_api_request(path_info):
    """True if any path segment marks this as an API-view request."""
    return bool(API_SEGMENTS.intersection(path_info.split("/")))


def allow_api_verbs(event):
    """IPubStart subscriber: clear maybe_webdav_client for API requests
    using PUT/PATCH/DELETE so they reach the API view.

    Genuine WebDAV requests to other content keep their flag, so real
    WebDAV is unaffected -- only API URLs are touched.
    """
    request = event.request
    method = request.get("REQUEST_METHOD", "GET").upper()
    if method not in WEBDAV_VERBS:
        return
    path_info = request.get("PATH_INFO", "") or ""
    if is_api_request(path_info):
        logger.debug(
            "Clearing maybe_webdav_client for API %s %s", method, path_info)
        request.maybe_webdav_client = 0
