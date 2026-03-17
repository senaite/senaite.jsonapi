FIELD PROJECTION
----------------

Running this test from the buildout directory:

    bin/test test_doctests -t field_projection


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from bika.lims import api

Functional Helpers:

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents

    >>> def get_count(response):
    ...     data = json.loads(response)
    ...     return data.get("count")

    >>> def get_item_keys(response, index=0):
    ...     data = json.loads(response)
    ...     items = data.get("items", [])
    ...     if not items:
    ...         return []
    ...     return sorted(items[index].keys())

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])

Create two Client objects and commit so they are indexed:

    >>> c1 = api.create(portal.clients, "Client", title="Alpha Lab", ClientID="AL")
    >>> c2 = api.create(portal.clients, "Client", title="Beta Lab", ClientID="BL")
    >>> uid1 = api.get_uid(c1)
    >>> uid2 = api.get_uid(c2)
    >>> transaction.commit()


Basic projection — only requested fields are returned
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requesting ``uid,id,title`` returns exactly those three keys in each item:

    >>> response = get("client?fields=uid,id,title")
    >>> keys = get_item_keys(response)
    >>> "uid" in keys
    True
    >>> "id" in keys
    True
    >>> "title" in keys
    True

Fields that were not requested are absent:

    >>> "portal_type" in keys
    False
    >>> "url" in keys
    False
    >>> "path" in keys
    False


Projection with complete=1
~~~~~~~~~~~~~~~~~~~~~~~~~~

Field projection applies after object wake-up, so ``complete=1`` fields
are also subject to it:

    >>> response = get("client?complete=1&fields=uid,title,ClientID")
    >>> keys = get_item_keys(response)
    >>> "uid" in keys
    True
    >>> "title" in keys
    True
    >>> "ClientID" in keys
    True

Fields outside the requested set are still excluded:

    >>> "id" in keys
    False
    >>> "portal_type" in keys
    False


Requested content is correct
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The projected values match the objects that were created:

    >>> response = get("client?fields=uid,title")
    >>> data = json.loads(response)
    >>> titles = sorted(item["title"] for item in data["items"])
    >>> titles
    [u'Alpha Lab', u'Beta Lab']


Projection with a single requested field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requesting only ``title`` returns items with exactly one key:

    >>> response = get("client?fields=title")
    >>> keys = get_item_keys(response)
    >>> keys
    [u'title']


Unknown fields are silently omitted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A field name that does not exist on the object is ignored rather than
raising an error:

    >>> response = get("client?fields=uid,nonexistent_field")
    >>> keys = get_item_keys(response)
    >>> "uid" in keys
    True
    >>> "nonexistent_field" in keys
    False


No projection when fields parameter is absent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without a ``fields`` parameter the full object is returned, including
the standard set of metadata fields:

    >>> response = get("client?uids={}".format(uid1))
    >>> keys = get_item_keys(response)
    >>> "uid" in keys
    True
    >>> "url" in keys
    True
    >>> "portal_type" in keys
    True


Projection combined with batch UID fetch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``?fields=`` and ``?uids=`` can be combined in a single request:

    >>> response = get("client?uids={},{}&fields=uid,title".format(uid1, uid2))
    >>> get_count(response)
    2
    >>> data = json.loads(response)
    >>> keys = sorted(data["items"][0].keys())
    >>> keys
    [u'title', u'uid']
    >>> "Alpha Lab" in response
    True
    >>> "Beta Lab" in response
    True


Projection on the generic /search route
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``fields`` parameter works on the ``/search`` endpoint as well:

    >>> response = get(
    ...     "search?portal_type=Client&fields=uid,id,title"
    ... )
    >>> keys = get_item_keys(response)
    >>> "uid" in keys
    True
    >>> "id" in keys
    True
    >>> "title" in keys
    True
    >>> "portal_type" in keys
    False
