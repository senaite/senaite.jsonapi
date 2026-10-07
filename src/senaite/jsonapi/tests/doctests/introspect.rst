INTROSPECT
----------

Introspection endpoints let a client discover the portal types, their schema
fields and the available workflow transitions without scraping the UI.

Running this test from the buildout directory:

    bin/test test_doctests -t introspect


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID

    >>> from bika.lims import api

Functional Helpers:

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, urllib.urlencode(data, doseq=True))
    ...     return browser.contents

    >>> def create(data):
    ...     response = post("create", data)
    ...     items = json.loads(response).get("items")
    ...     return api.get_object(items[0]["uid"])

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Create a client to introspect:

    >>> clients = api.get_portal().clients
    >>> data = {"portal_type": "Client",
    ...         "parent_path": api.get_path(clients),
    ...         "title": "Chicken Corp",
    ...         "ClientID": "CC"}
    >>> client = create(data)


Types
~~~~~

List the registered portal types:

    >>> response = get("types")
    >>> data = json.loads(response)
    >>> "Client" in [t["portal_type"] for t in data["items"]]
    True

Describe a single portal type. The detail includes the catalogs that index
the type and the permission required to add it:

    >>> response = get("types/Client")
    >>> data = json.loads(response)
    >>> data["portal_type"]
    u'Client'

    >>> isinstance(data["catalogs"], list) and len(data["catalogs"]) > 0
    True

    >>> "add_permission" in data
    True

An unknown portal type returns a 404:

    >>> get("types/NoSuchType")
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 404: Not Found


Schema
~~~~~~

Describe the schema fields of a portal type:

    >>> response = get("schema/Client")
    >>> data = json.loads(response)
    >>> data["portal_type"]
    u'Client'

    >>> field_names = [f["name"] for f in data["fields"]]
    >>> "ClientID" in field_names
    True

The `ClientID` field is required:

    >>> client_id = [f for f in data["fields"] if f["name"] == "ClientID"][0]
    >>> client_id["required"]
    True


Workflow
~~~~~~~~

Return the current state and the available transitions of an object:

    >>> uid = api.get_uid(client)
    >>> response = get("workflow/{}".format(uid))
    >>> data = json.loads(response)
    >>> data["review_state"]
    u'active'

    >>> "deactivate" in [t["id"] for t in data["transitions"]]
    True

An unknown uid returns a 404:

    >>> get("workflow/no-such-uid")
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 404: Not Found
