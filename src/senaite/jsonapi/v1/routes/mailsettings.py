from senaite.jsonapi import api
from senaite.jsonapi import request as req
from senaite.jsonapi.v1 import add_route


@add_route("/mailsettings", "senaite.jsonapi.v1.mailsettings", methods=["GET"])
def get(context, request):
    """Return the mail configuration
    """
    mail_settings = api.get_mail_settings()

    # Prepare batch
    size = req.get_batch_size()
    start = req.get_batch_start()
    batch = api.make_batch(mail_settings, size, start)

    return {
        "pagesize": batch.get_pagesize(),
        "next": batch.make_next_url(),
        "previous": batch.make_prev_url(),
        "page": batch.get_pagenumber(),
        "pages": batch.get_numpages(),
        "count": batch.get_sequence_length(),
        "items": [mail_settings],
        "url": api.url_for("senaite.jsonapi.v1.mailsettings"),
    }
