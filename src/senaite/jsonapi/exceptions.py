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

"""Typed exception classes for the SENAITE JSON API.

Every subclass of `APIError` carries a default HTTP status so route
code can `raise NotFoundError("...")` instead of `api.fail(404, ...)`.
The class name reaches the client verbatim as the `type` field of the
JSON error envelope (see senaite/senaite.core#2998), letting clients
distinguish "not found" from "unauthorized" from a validation error
without parsing free-form text.

Backward compatibility: every typed error inherits `APIError`, so any
code that catches `APIError` still catches all of them, and the legacy
`api.fail(status, msg)` helper still raises a plain `APIError`.

The status is carried, not applied. It reaches the response when
plone.jsonapi.core renders the error envelope, which is the moment the
error becomes the answer. Setting it in the constructor instead meant
an error that was caught, and never answered with, still left its
status on whatever the request went on to return.
"""

from senaite.jsonapi import request as req


class APIError(Exception):
    """Base class for every JSON API error.

    Instances carry an HTTP status code and a human-facing message.
    """
    status = 500

    def __init__(self, message, status=None):
        if status is not None:
            self.status = status
        self.message = message

    def _set_response_status(self, status):
        request = req.getRequest()
        # req.getRequest() may return None outside a real request
        # context (unit tests, setup handlers). Skip silently in that
        # case so setting a status never crashes ancillary code.
        if request is None:
            return
        response = getattr(request, "response", None)
        if response is None:
            return
        response.setStatus(status)

    # Legacy alias, retained so existing callers of `err.setStatus(x)`
    # keep working. Nothing in this package calls it: the status of an
    # error reaches the response when the envelope is rendered.
    def setStatus(self, status):
        self.status = status
        self._set_response_status(status)

    def __str__(self):
        return self.message


class BadRequestError(APIError):
    """400 — the request payload is malformed or missing required fields.

    Use for JSON parse failures, missing keys the caller must supply,
    or query parameters that fail structural validation.
    """
    status = 400


class UnauthorizedError(APIError):
    """401 — the caller is not authenticated.

    Distinct from `ForbiddenError`: 401 means "log in and try again",
    403 means "you are logged in but you may not do this".
    """
    status = 401


class ForbiddenError(APIError):
    """403 — the caller is authenticated but lacks the required
    permission.
    """
    status = 403


class NotFoundError(APIError):
    """404 — the addressed resource does not exist."""
    status = 404


class ConflictError(APIError):
    """409 — the request conflicts with the current state of the
    resource (for example, creating an object with a duplicate id).
    """
    status = 409


class ValidationError(APIError):
    """422 — the payload was well-formed but semantically invalid.

    Use for schema validation failures, unknown enum values, or
    business-rule violations detected during create/update.
    """
    status = 422
