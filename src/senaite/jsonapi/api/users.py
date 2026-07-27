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

"""User-related helpers.

Kept as thin wrappers over `plone.api.user` so the rest of the codebase
does not have to reach across two `api` namespaces
(`senaite.jsonapi.api` and `plone.api`) to answer basic user questions.
"""

from bika.lims import api as bika_api
from plone import api as ploneapi

from senaite.jsonapi import underscore as u


def is_anonymous():
    """Return True if the current user is not authenticated."""
    return ploneapi.user.is_anonymous()


def get_current_user():
    """Return the current logged-in Plone MemberData."""
    return ploneapi.user.get_current()


def get_member_ids():
    """Return all member ids of the portal."""
    pm = bika_api.get_tool("portal_membership")
    # portal_membership may return None entries for stale/broken accounts
    return filter(lambda x: x, pm.listMemberIds())


def get_user(user_or_username=None):
    """Return the Plone MemberData for a user or user id.

    Accepts a MemberData, a userid string, or None (returns None).
    """
    if user_or_username is None:
        return None
    if hasattr(user_or_username, "getUserId"):
        return ploneapi.user.get(user_or_username.getUserId())
    return ploneapi.user.get(userid=u.to_string(user_or_username))


def get_user_properties(user_or_username):
    """Return all property-sheet properties for the user as a dict."""
    user = get_user(user_or_username)
    if user is None:
        return {}
    if not callable(user.getUser):
        return {}
    out = {}
    plone_user = user.getUser()
    for sheet in plone_user.listPropertysheets():
        ps = plone_user.getPropertysheet(sheet)
        out.update(dict(ps.propertyItems()))
    return out
