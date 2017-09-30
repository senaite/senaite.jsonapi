# -*- coding: utf-8 -*-

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
