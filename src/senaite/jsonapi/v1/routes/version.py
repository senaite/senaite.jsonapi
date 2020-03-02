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

from senaite.jsonapi import url_for
from senaite.jsonapi import add_route

from senaite.jsonapi.v1 import __version__
from senaite.jsonapi.v1 import __date__


@add_route("/senaite/v1", "senaite.jsonapi.v1.version", methods=["GET"])
@add_route("/senaite/v1/version", "senaite.jsonapi.v1.version", methods=["GET"])
def version(context, request):
    """get the version, build number and date of this API
    """
    return {
        "url":     url_for("senaite.jsonapi.v1.version"),
        "version": __version__,
        "date":    __date__,
    }
