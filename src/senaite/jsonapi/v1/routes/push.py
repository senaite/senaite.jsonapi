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
from senaite.jsonapi.interfaces import IPushConsumer
from senaite.jsonapi.v1 import add_route
from zope.component import queryAdapter


@add_route("/push", "senaite.jsonapi.v1.push", methods=["POST"])
def push(context, request):

    # disable CSRF
    req.disable_csrf_protection()

    # Cannot push being an anonymous user!
    if api.is_anonymous():
        api.fail(401, "Anonymous user")

    # extract the data from the request
    records = req.get_request_data()
    if not records:
        api.fail(500, "No data sent")

    if len(records) > 1:
        api.fail(500, "Push with multiple entries is not supported")

    # Get the record containing the data for this push
    record = records[0]

    # Name of the adapter that will be able to handle this POST data
    name = record.get("consumer")
    if not name:
        api.fail(500, "No consumer name provided")

    consumer = queryAdapter(record, IPushConsumer, name=name)
    if consumer is None:
        api.fail(500, "No consumer registered for name={}".format(name))

    try:
        success = consumer.process()
    except Exception as e:
        api.fail(500, e.message)

    return {
        "url": api.url_for("senaite.jsonapi.v1.push"),
        "success": success,
    }
