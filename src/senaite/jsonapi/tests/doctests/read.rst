READ
----

Running this test from the buildout directory:

    bin/test test_doctests -t read


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

    >>> from bika.lims import api

Functional Helpers:

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents

    >>> def get_count(response):
    ...     data = json.loads(response)
    ...     return data.get("count")

    >>> def get_items_ids(response, sort=True):
    ...     data = json.loads(response)
    ...     items = data.get("items")
    ...     items = map(lambda it: it["id"], items)
    ...     if sort:
    ...         return sorted(items)
    ...     return items

    >>> def init_data():
    ...     api.create(portal.clients, "Client", title="Happy Hills", ClientID="HH")
    ...     api.create(portal.clients, "Client", title="ACME", ClientID="AC")
    ...     api.create(portal.clients, "Client", title="Fill the gap", ClientID="FG")
    ...     transaction.commit()

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Initialize the instance with some objects for testing:

    >>> init_data()


Get resource objects
~~~~~~~~~~~~~~~~~~~~

We can get the objects from a resource type:

    >>> response = get("client")
    >>> get_count(response)
    3
    >>> get_items_ids(response)
    [u'client-1', u'client-2', u'client-3']

Get by uid
~~~~~~~~~~

We can directly fetch a given object by it's UID and resource:

    >>> client = api.create(portal.clients, "Client", title="Woow", ClientID="WO")
    >>> uid = api.get_uid(client)
    >>> transaction.commit()
    >>> response = get("client/{}".format(uid))
    >>> get_count(response)
    1
    >>> response
    '..."title": "Woow"...'

Even with only the uid:

    >>> response = get(uid)
    >>> response
    '..."title": "Woow"...'

but with no items in the response:

    >>> "items" in response
    False

    >>> sorted(json.loads(response).keys())
    [u'AccountName', u'AccountNumber', u'AccountType',...]
