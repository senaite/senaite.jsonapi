SEARCH
------

Running this test from the buildout directory:

    bin/test test_doctests -t search


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import transaction
    >>> import urllib

    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

    >>> from bika.lims import api

Functional Helpers:

    >>> def login(user=TEST_USER_ID, password=TEST_USER_PASSWORD):
    ...     browser.open(portal_url + "/login_form")
    ...     browser.getControl(name='__ac_name').value = user
    ...     browser.getControl(name='__ac_password').value = password
    ...     browser.getControl(name='submit').click()
    ...     assert("__ac_password" not in browser.contents)

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents

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

Authenticate:

    >>> login()

We can directly search by resource:

    >>> get("client")
    '{"count": 3, ... "id": "client-1", ...}'

We can also add search criteria as well:

    >>> get("client?id=client-1")
    '{"count": 1, ..."id": "client-1", ...}'
    >>> get("client?getName=ACME")
    '{"count": 1, ..."id": "client-2", ...}'


Sort and limit
~~~~~~~~~~~~~~

We can use sort and limit too:

    >>> get("client?sort_on=id&sort_order=asc")
    '{"count": 3, ..."id": "client-1", ..."id": "client-2", ..."id": "client-3", ...}'
    >>> get("client?sort_on=id&sort_order=desc")
    '{"count": 3, ..."id": "client-3", ..."id": "client-2", ..."id": "client-1", ...}'
    >>> get("client?sort_on=id&sort_order=desc&limit=2")
    '{"count": 3, "pagesize": 2, ..."id": "client-3", ...}'


Search without resource
~~~~~~~~~~~~~~~~~~~~~~~

We can also omit the resource and search directly by portal_type:

    >>> get("search?portal_type=Client")
    '{"count": 3, ..."id": "client-1", ...}'

Additional search criteria and sorting works as well:

    >>> get("search?portal_type=Client&getName=ACME")
    '{"count": 1, ..."id": "client-2", ...}'
    >>> get("search?portal_type=Client&sort_on=id&sort_order=desc&limit=2")
    '{"count": 3, "pagesize": 2, ..."id": "client-3", ...}'


Catalog search
~~~~~~~~~~~~~~

We can specify the catalog to use in searches. Sample Types are stored in both
portal_catalog and setup_catalog:

    >>> get("sampletype")
    '{"count": 2, ... "id": "sampletype-1", ...}'
    >>> get("sampletype?catalog=portal_catalog")
    '{"count": 2, ... "id": "sampletype-1", ...}'
    >>> get("sampletype?catalog=bika_setup_catalog")
    '{"count": 2, ... "id": "sampletype-1", ...}'

But Sample Types are not stored in "bika_catalog":

    >>> get("sampletype?catalog=bika_catalog")
    '{"count": 0, ...}'
