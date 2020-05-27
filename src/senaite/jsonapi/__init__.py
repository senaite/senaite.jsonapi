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

import logging

from plone.jsonapi.core import router

PRODUCT_NAME = "senaite.jsonapi"

logger = logging.getLogger("senaite.jsonapi")


def add_route(route, endpoint=None, **kw):
    """Add a new JSON API route
    """
    def wrapper(f):
        try:
            router.DefaultRouter.add_url_rule(route,
                                              endpoint=endpoint,
                                              view_func=f,
                                              options=kw)
        except AssertionError, e:
            logger.warn("Failed to register route {}: {}".format(route, e))
        return f
    return wrapper


def url_for(endpoint, default="senaite.jsonapi.get", **values):
    """Looks up the API URL for the given endpoint

    :param endpoint: The name of the registered route (aka endpoint)
    :type endpoint: string
    :returns: External URL for this endpoint
    :rtype: string/None
    """

    try:
        return router.url_for(endpoint, force_external=True, values=values)
    except Exception:
        # XXX plone.jsonapi.core should catch the BuildError of Werkzeug and
        #     throw another error which can be handled here.
        logger.debug("Could not build API URL for endpoint '%s'. "
                     "No route provider registered?" % endpoint)

        # build generic API URL
        return router.url_for(default, force_external=True, values=values)
