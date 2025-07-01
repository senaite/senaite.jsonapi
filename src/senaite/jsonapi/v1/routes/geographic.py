# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.JSONAPI.
#
# SENAITE.JSONAPI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2017-2025 by it's authors.
# Some rights reserved, see README and LICENSE.

from senaite.jsonapi import add_route
from senaite.jsonapi import request as req
from senaite.core.api import geo


def create_subdivision_dict(
    subdivision, parent_name, depth,
):
    """
    Create a standardized subdivision dictionary
    """
    return {
        "code": subdivision.code,
        "name": subdivision.name,
        "type": subdivision.type,
        "country_code": subdivision.country_code,
        "parent_code": (
            subdivision.parent_code
            if depth == 2 else subdivision.country_code
        ),
        "parent": parent_name,
        "depth": depth,
    }


def get_level2_subdivisions(level1_subdivision):
    """
    Get level 2 subdivisions for a given level 1 subdivision
    """
    return geo.get_subdivisions(level1_subdivision, default=[])


def get_all_subdivisions(depth=None):
    """
    Get all subdivisions from all countries at specified depth
    """
    countries = geo.get_countries()
    all_subdivisions = []

    for country in countries:
        # Get level 1 subdivisions (states/provinces)
        level1_subdivisions = geo.get_subdivisions(country, default=[])
        for subdivision in level1_subdivisions:
            # Only add level 1 if depth is None, 0, or 1
            if depth is None or depth == 0 or depth == 1:
                all_subdivisions.append(
                    create_subdivision_dict(
                        subdivision=subdivision,
                        parent_name=country.name,
                        depth=1,
                    )
                )

            # Get level 2 subdivisions (counties/districts) for this
            # subdivision
            # Only add level 2 if depth is None, 0, or 2
            if depth is None or depth == 0 or depth == 2:
                level2_subdivisions = get_level2_subdivisions(subdivision)
                for sub_subdivision in level2_subdivisions:
                    all_subdivisions.append(
                        create_subdivision_dict(
                            subdivision=sub_subdivision,
                            parent_name=subdivision.name,
                            depth=2,
                        )
                    )

    return all_subdivisions


def get_country_subdivisions(country_code, depth):
    """
    Get subdivisions for a specific country and depth
    """
    # Get country by code
    geo_country = geo.get_country(country_code, default=None)
    if not geo_country:
        return {
            "count": 0,
            "items": [],
            "error": "Country not found: {}".format(country_code),
            "depth": None if depth < 0 else depth,
        }

    # Get level 1 subdivisions for the country
    level1_subdivisions = geo.get_subdivisions(country_code, default=[])
    items = []

    if depth == 1:
        # Only level 1 subdivisions
        for subdivision in level1_subdivisions:
            items.append(
                create_subdivision_dict(
                    subdivision=subdivision,
                    parent_name=geo_country.name,
                    depth=1,
                )
            )
    elif depth == 2:
        # Only level 2 subdivisions
        for subdivision in level1_subdivisions:
            level2_subdivisions = get_level2_subdivisions(subdivision)
            for sub_subdivision in level2_subdivisions:
                items.append(
                    create_subdivision_dict(
                        subdivision=sub_subdivision,
                        parent_name=subdivision.name,
                        depth=2,
                    )
                )
    else:
        # All depths (both 1 and 2)
        for subdivision in level1_subdivisions:
            items.append(
                create_subdivision_dict(
                    subdivision=subdivision,
                    parent_name=geo_country.name,
                    depth=1,
                )
            )
            level2_subdivisions = get_level2_subdivisions(subdivision)
            for sub_subdivision in level2_subdivisions:
                items.append(
                    create_subdivision_dict(
                        subdivision=sub_subdivision,
                        parent_name=subdivision.name,
                        depth=2,
                    )
                )

    return {
        "count": len(items),
        "items": items,
        "country": country_code,
        "depth": None if depth < 0 else depth,
    }


@add_route("/senaite/v1",
           "senaite.jsonapi.v1.geographic", methods=["GET"])
@add_route("/senaite/v1/geographic/subdivisions_schema",
           "senaite.jsonapi.v1.geographic", methods=["GET"])
def get(context, request):
    """
    Get subdivisions based on the country code
        <Plonesite>/@@API/v1/geographic/subdivisions_schema
            ->returns all subdivisions
        <Plonesite>/@@API/v1/geographic/subdivisions_schema?country=Code
            ->returns only that country
        <Plonesite>/@@API/v1/geographic/subdivisions_schema?country=Code&depth=Level
            ->returns only that country and depth
        <Plonesite>/@@API/v1/geographic/subdivisions_schema?depth=Level
            ->returns all subdivisions at specified depth
    """
    country = req.get_country()
    depth = req.get_depth()

    # If no country provided, return all subdivisions at specified depth
    if not country:
        all_subdivisions = get_all_subdivisions(depth)
        return {
            "count": len(all_subdivisions),
            "items": all_subdivisions,
            "depth": None if depth < 0 else depth,
        }

    # Get subdivisions for specific country and depth
    return get_country_subdivisions(country, depth)
