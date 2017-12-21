# -*- coding: utf-8 -*-

from senaite.jsonapi import api
from senaite.jsonapi import request as req
from senaite.jsonapi.v1 import add_route


@add_route("/registry", "senaite.jsonapi.v1.registry", methods=["GET"])
@add_route("/registry/<string:key>", "senaite.jsonapi.v1.registry", methods=["GET"])
def get(context, request, key=None):
    """Return all registry items if key is None, otherwise try to fetch the registry key
    """
    registry_records = api.get_registry_records_by_keyword(key)

    # Prepare batch
    size = req.get_batch_size()
    start = req.get_batch_start()
    batch = api.make_batch(registry_records, size, start)

    return {
        "pagesize": batch.get_pagesize(),
        "next": batch.make_next_url(),
        "previous": batch.make_prev_url(),
        "page": batch.get_pagenumber(),
        "pages": batch.get_numpages(),
        "count": batch.get_sequence_length(),
        "items": [registry_records],
        "url": api.url_for("senaite.jsonapi.v1.registry", key=key),
    }
