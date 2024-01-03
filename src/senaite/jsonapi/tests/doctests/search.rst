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
    ...     api.create(setup.bika_sampletypes, "SampleType", title="Water", Prefix="W")
    ...     api.create(setup.bika_sampletypes, "SampleType", title="Dust", Prefix="D")
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
