BATCH FETCH BY UID
------------------

Running this test from the buildout directory:

    bin/test test_doctests -t batch_fetch


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

    >>> def get_items_ids(response, sort=True):
    ...     data = json.loads(response)
    ...     items = data.get("items")
    ...     items = map(lambda it: it["id"], items)
    ...     if sort:
    ...         return sorted(items)
    ...     return list(items)

    >>> def get_items_uids(response):
    ...     data = json.loads(response)
    ...     items = data.get("items")
    ...     return sorted(it["uid"] for it in items)

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])

Create three Client objects and commit so they are indexed:

    >>> c1 = api.create(portal.clients, "Client", title="Alpha Lab", ClientID="AL")
    >>> c2 = api.create(portal.clients, "Client", title="Beta Lab", ClientID="BL")
    >>> c3 = api.create(portal.clients, "Client", title="Gamma Lab", ClientID="GL")
    >>> uid1 = api.get_uid(c1)
    >>> uid2 = api.get_uid(c2)
    >>> uid3 = api.get_uid(c3)
    >>> transaction.commit()


Batch fetch two objects by UID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Passing a comma-separated ``uids`` parameter returns only the matching
objects in a single request:

    >>> response = get("client?uids={},{}".format(uid1, uid2))
    >>> get_count(response)
    2
    >>> get_items_ids(response)
    [u'client-1', u'client-2']

The third client is not included because its UID was not requested:

    >>> "Gamma Lab" in response
    False


Batch fetch all three objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> response = get("client?uids={},{},{}".format(uid1, uid2, uid3))
    >>> get_count(response)
    3
    >>> get_items_ids(response)
    [u'client-1', u'client-2', u'client-3']


Batch fetch a single UID via the uids parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A single-item list is valid and returns one object wrapped in the
standard batched response (with ``items`` and ``count``):

    >>> response = get("client?uids={}".format(uid1))
    >>> get_count(response)
    1
    >>> get_items_ids(response)
    [u'client-1']

    >>> "items" in response
    True


Returned UIDs match the requested UIDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> response = get("client?uids={},{}".format(uid2, uid3))
    >>> returned = get_items_uids(response)
    >>> returned == sorted([uid2, uid3])
    True


Batch fetch works with complete=1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding ``complete=1`` wakes up the objects and returns full field data:

    >>> response = get("client?uids={},{}&complete=1".format(uid1, uid2))
    >>> get_count(response)
    2
    >>> "Alpha Lab" in response
    True
    >>> "Beta Lab" in response
    True


Batch fetch respects portal_type scoping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using a typed resource route (``/client``), the portal_type
constraint is applied alongside the UID filter. UIDs belonging to a
different portal type are not returned.

Create a SampleType to obtain a non-Client UID:

    >>> st = api.create(portal.setup.sampletypes, "SampleType", title="Blood", Prefix="BL")
    >>> uid_st = api.get_uid(st)
    >>> transaction.commit()

Fetching via ``/client?uids=`` with a SampleType UID returns no items:

    >>> response = get("client?uids={}".format(uid_st))
    >>> get_count(response)
    0


Batch fetch via the generic /search route
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``uids`` parameter also works on the generic ``/search`` endpoint
when combined with ``portal_type``:

    >>> response = get(
    ...     "search?portal_type=Client&uids={},{}".format(uid1, uid3)
    ... )
    >>> get_count(response)
    2
    >>> get_items_ids(response)
    [u'client-1', u'client-3']
