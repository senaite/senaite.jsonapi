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

from bika.lims.utils.analysisrequest import create_partition
from senaite.jsonapi import api
from senaite.jsonapi import request as req
from senaite.jsonapi.api import fail
from senaite.jsonapi.api import make_items_for
from senaite.jsonapi.v1 import add_route

# keys of a partition spec that are not passed straight to create_partition
PARTITION_KWARGS = ("analyses", "sample_type", "container", "preservation",
                    "internal_use")


def create_one_partition(primary_uid, spec, request):
    """Create a single partition of the primary sample

    :param primary_uid: UID of the primary (root) sample
    :param spec: mapping with the partition specific values
    :param request: the current request object
    :returns: the new partition sample
    """
    kwargs = {
        "request": request,
        "analysis_request": primary_uid,
        "analyses": spec.get("analyses", []),
        "sample_type": spec.get("sample_type"),
        "container": spec.get("container"),
        "preservation": spec.get("preservation"),
    }
    # only override the core default when the caller is explicit
    if "internal_use" in spec:
        kwargs["internal_use"] = spec.get("internal_use")
    return create_partition(**kwargs)


@add_route("/partition", "senaite.jsonapi.v1.partition", methods=["POST"])
def partition(context, request):
    """Create one or more partitions (aliquots) of a received sample

    POST body::

        {"uid": "<primary sample uid>",
         "partitions": [
            {"analyses": ["<analysis uid>", ...],
             "sample_type": "<uid>",     # optional, defaults to the primary
             "container": "<uid>",       # optional
             "preservation": "<uid>",    # optional
             "internal_use": false},     # optional
            ...
         ]}

    A single partition may be given inline without the `partitions` wrapper::

        {"uid": "<primary sample uid>", "analyses": ["<analysis uid>", ...]}

    Creating a partition without analyses is allowed; analyses can be added
    later. The selected analyses are moved from the primary into the
    partition.
    """
    req.disable_csrf_protection()

    records = req.get_request_data()
    created = []

    for record in records:
        primary_uid = record.get("uid")
        if not primary_uid:
            fail(400, "A primary sample 'uid' is required")
        if api.get_object_by_uid(primary_uid, None) is None:
            fail(404, "No sample found for uid '{}'".format(primary_uid))

        specs = record.get("partitions")
        if not specs:
            # treat the record itself as a single partition spec
            specs = [record]

        for spec in specs:
            created.append(create_one_partition(primary_uid, spec, request))

    if not created:
        fail(400, "No partitions could be created")

    items = make_items_for(created)
    return {
        "count": len(items),
        "items": items,
        "url": api.url_for("senaite.jsonapi.v1.partition"),
    }
