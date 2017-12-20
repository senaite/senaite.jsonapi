# -*- coding: utf-8 -*-

from senaite.jsonapi import api
from senaite.jsonapi import request as req
from senaite.jsonapi.v1 import add_route


@add_route("/bika-config-registry", "senaite.jsonapi.v1.bika-config-registry", methods=["GET"])
@add_route("/registry/bika-config-registry", "senaite.jsonapi.v1.registry.bika-config-registry", methods=["GET"])
def get(context, request, username=None):
    """Bika and Senaite configuration registry records route
    """
    registry_records = api.get_registry_records_by_keyword("bika")
    registry_records.update(api.get_registry_records_by_keyword("senaite"))

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
        "items": registry_records,
    }
