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

from senaite.jsonapi import api
from senaite.jsonapi import request as req
from senaite.jsonapi.v1 import add_route


@add_route("/catalogs", "senaite.jsonapi.v1.catalogs", methods=["GET"])
@add_route("/catalogs/<string:key>", "senaite.jsonapi.v1.catalogs", methods=["GET"])
def get(context, request, key=None):
    """Returns all registered catalogs if key is None, otherwise try to fetch
    the information about the catalog name passed in
    """
    # Get the catalogs
    if key:
        catalogs = [api.get_tool(key)]
    else:
        archetype_tool = api.get_tool("archetype_tool")
        if not archetype_tool:
            # Default catalog
            catalogs = [api.get_tool("portal_catalog")],
        else:
            catalogs = archetype_tool.getCatalogsInSite()
            catalogs = map(api.get_tool, catalogs)

    def get_data(catalog):
        return {
            "id": catalog.id,
            "indexes": catalog.indexes(),
            "schema": catalog.schema(),
            "portal_types": catalog.getPortalTypes(),
        }

    # Exclude some catalogs
    skip = ["reference_catalog", "uid_catalog"]
    catalogs = filter(lambda cat: cat.id not in skip, catalogs)

    # Generate the metadata info for catalogs
    records = map(get_data, catalogs)

    # Prepare batch
    size = req.get_batch_size()
    start = req.get_batch_start()
    batch = api.make_batch(records, size, start)

    return {
        "pagesize": batch.get_pagesize(),
        "next": batch.make_next_url(),
        "previous": batch.make_prev_url(),
        "page": batch.get_pagenumber(),
        "pages": batch.get_numpages(),
        "count": batch.get_sequence_length(),
        "items": records,
        "url": api.url_for("senaite.jsonapi.v1.registry", key=key),
    }
