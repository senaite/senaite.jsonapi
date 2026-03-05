SEARCH
------

Running this test from the buildout directory:

    bin/test test_doctests -t search


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
    ...     api.create(portal.setup.sampletypes, "SampleType", title="Water", Prefix="W")
    ...     api.create(portal.setup.sampletypes, "SampleType", title="Dust", Prefix="D")
    ...     transaction.commit()

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setup = api.get_setup()
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])

Initialize the instance with some objects for testing:

    >>> init_data()


Basic search
~~~~~~~~~~~~

We can directly search by resource:

    >>> response = get("client")
    >>> get_count(response)
    3
    >>> get_items_ids(response)
    [u'client-1', u'client-2', u'client-3']

We can also add search criteria as well:

    >>> response = get("client?id=client-1")
    >>> get_count(response)
    1
    >>> get_items_ids(response)
    [u'client-1']

    >>> response = get("client?getName=ACME")
    >>> get_count(response)
    1
    >>> get_items_ids(response)
    [u'client-2']


Sort and limit
~~~~~~~~~~~~~~

We can use sort and limit too:

    >>> response = get("client?sort_on=id&sort_order=asc")
    >>> get_items_ids(response, sort=False)
    [u'client-1', u'client-2', u'client-3']

    >>> response = get("client?sort_on=id&sort_order=desc")
    >>> get_items_ids(response, sort=False)
    [u'client-3', u'client-2', u'client-1']

    >>> response = get("client?sort_on=id&sort_order=desc&limit=2")
    >>> get_items_ids(response, sort=False)
    [u'client-3', u'client-2']


Search without resource
~~~~~~~~~~~~~~~~~~~~~~~

We can also omit the resource and search directly by portal_type:

    >>> response = get("search?portal_type=Client")
    >>> get_items_ids(response)
    [u'client-1', u'client-2', u'client-3']

Additional search criteria and sorting works as well:

    >>> response = get("search?portal_type=Client&getName=ACME")
    >>> get_items_ids(response)
    [u'client-2']

    >>> response = get("search?portal_type=Client&sort_on=id&sort_order=desc&limit=2")
    >>> get_items_ids(response, sort=False)
    [u'client-3', u'client-2']


Catalog search
~~~~~~~~~~~~~~

We can specify the catalog to use in searches. Sample Types are stored in both
portal_catalog and setup_catalog:

    >>> response = get("sampletype")
    >>> get_items_ids(response)
    [u'sampletype-1', u'sampletype-2']

    >>> response = get("sampletype?catalog=senaite_catalog_setup")
    >>> get_items_ids(response)
    [u'sampletype-1', u'sampletype-2']

But Sample Types are not stored in "senaite_catalog":

    >>> response = get("sampletype?catalog=senaite_catalog")
    >>> get_items_ids(response)
    []


Sorting by created and modified with second-level precision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When sorting by 'created' or 'modified' indexes, the sorting should have
second-level precision, not just minute-level precision. This ensures accurate
ordering of items created or modified within the same minute.

Let's test this by creating multiple sample types in quick succession:

    >>> import time
    >>> from DateTime import DateTime

Create sample types with controlled timestamps to test second-level precision:

    >>> st1 = api.create(portal.setup.sampletypes, "SampleType", title="Alpha", Prefix="A")
    >>> time.sleep(2)
    >>> st2 = api.create(portal.setup.sampletypes, "SampleType", title="Beta", Prefix="B")
    >>> time.sleep(2)
    >>> st3 = api.create(portal.setup.sampletypes, "SampleType", title="Gamma", Prefix="G")
    >>> transaction.commit()

Verify the creation dates differ at second level:

    >>> created1 = api.get_creation_date(st1)
    >>> created2 = api.get_creation_date(st2)
    >>> created3 = api.get_creation_date(st3)
    >>> created1 < created2 < created3
    True

Now search sorted by created date in ascending order:

    >>> response = get("sampletype?sort_on=created&sort_order=asc")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> len(items) >= 3
    True

The items should be sorted with second-level precision. Let's verify the newly
created items are in the correct order:

    >>> titles = ["Alpha", "Beta", "Gamma"]
    >>> recent_items = [it for it in items if it["title"] in titles]
    >>> [it["title"] for it in recent_items]
    [u'Alpha', u'Beta', u'Gamma']

Verify that the 'created' timestamps in the response are in ascending order:

    >>> recent_created = [DateTime(it["created"]) for it in recent_items]
    >>> recent_created[0] <= recent_created[1] <= recent_created[2]
    True

Now test descending order:

    >>> response = get("sampletype?sort_on=created&sort_order=desc")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> recent_items = [it for it in items if it["title"] in titles]
    >>> [it["title"] for it in recent_items]
    [u'Gamma', u'Beta', u'Alpha']

Filtering by created_since with second-level precision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DateIndex only stores minute-level precision, so two objects created seconds
apart may share the same index value. The ``created_since`` parameter must
post-filter by the actual metadata to achieve second-level accuracy.

    >>> from urllib import quote

Using Beta's creation time as cutoff returns Beta and Gamma (inclusive):

    >>> cutoff = quote(created2.ISO8601())
    >>> response = get("sampletype?created_since={}".format(cutoff))
    >>> data = json.loads(response)
    >>> items = data.get("items") or []
    >>> sorted([it["title"] for it in items if it["title"] in titles])
    [u'Beta', u'Gamma']

Using Gamma's creation time as cutoff returns only Gamma:

    >>> cutoff = quote(created3.ISO8601())
    >>> response = get("sampletype?created_since={}".format(cutoff))
    >>> data = json.loads(response)
    >>> items = data.get("items") or []
    >>> sorted([it["title"] for it in items if it["title"] in titles])
    [u'Gamma']

Using Alpha's creation time as cutoff returns all three:

    >>> cutoff = quote(created1.ISO8601())
    >>> response = get("sampletype?created_since={}".format(cutoff))
    >>> data = json.loads(response)
    >>> items = data.get("items") or []
    >>> sorted([it["title"] for it in items if it["title"] in titles])
    [u'Alpha', u'Beta', u'Gamma']

A future cutoff returns none of our items:

    >>> future = quote(DateTime(created3 + 1.0 / 86400).ISO8601())
    >>> response = get("sampletype?created_since={}".format(future))
    >>> data = json.loads(response)
    >>> items = data.get("items") or []
    >>> [it["title"] for it in items if it["title"] in titles]
    []


Sorting by modified with second-level precision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The catalog sorts DateIndex results manually to achieve second-level precision.

Create sample types and modify them with clear time separation:

    >>> stm1 = api.create(portal.setup.sampletypes, "SampleType", title="ModAlpha", Prefix="MA")
    >>> time.sleep(2)
    >>> stm2 = api.create(portal.setup.sampletypes, "SampleType", title="ModBeta", Prefix="MB")
    >>> time.sleep(2)
    >>> stm3 = api.create(portal.setup.sampletypes, "SampleType", title="ModGamma", Prefix="MG")
    >>> transaction.commit()

Modify the objects with delays to ensure distinct modification timestamps:

    >>> stm1.setDescription("Modified first")
    >>> stm1.reindexObject()
    >>> time.sleep(2)
    >>> stm2.setDescription("Modified second")
    >>> stm2.reindexObject()
    >>> time.sleep(2)
    >>> stm3.setDescription("Modified third")
    >>> stm3.reindexObject()
    >>> transaction.commit()

Search sorted by modified date in ascending order:

    >>> titles = ["ModAlpha", "ModBeta", "ModGamma"]
    >>> response = get("sampletype?sort_on=modified&sort_order=asc")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> mod_items = [it for it in items if it["title"] in titles]
    >>> len(mod_items) == 3
    True

Verify the modification timestamps are returned and in ascending order.
The catalog's manual sorting ensures they're sorted by the metadata column:

    >>> mod_times = [DateTime(it["modified"]) for it in mod_items]
    >>> mod_times[0] <= mod_times[1] <= mod_times[2]
    True

Test descending order for modified:

    >>> response = get("sampletype?sort_on=modified&sort_order=desc")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> mod_items_desc = [it for it in items if it["title"] in titles]
    >>> len(mod_items_desc) == 3
    True

Verify timestamps are in descending order:

    >>> mod_times_desc = [DateTime(it["modified"]) for it in mod_items_desc]
    >>> mod_times_desc[0] >= mod_times_desc[1] >= mod_times_desc[2]
    True

Note: ``modified_since`` filtering cannot be tested with SampleType objects
because ``senaite_catalog_setup`` does not include ``modified`` as a metadata
column. The post-filter gracefully skips fields not in the catalog schema.
