CATALOGS
--------

Running this test from the buildout directory:

    bin/test test_doctests -t catalogs


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
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


Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setup = api.get_setup()
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Get all catalogs
~~~~~~~~~~~~~~~~

`senaite.jsonapi` is capable to retrieve information about the catalogs
registered in the system:

    >>> response = get("catalogs")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> catalog_ids = map(lambda cat: cat["id"], items)
    >>> sorted(catalog_ids)
    [u'auditlog_catalog', ..., u'portal_catalog']

Catalogs for internal use are not included though:

    >>> "uid_catalog" in catalog_ids
    False

    >>> "reference_catalog" in catalog_ids
    False

For each catalog, indexes, schema fields and allowed portal types are listed:

    >>> cat = filter(lambda it: it["id"]=="portal_catalog", items)[0]
    >>> sorted(cat.get("indexes"))
    [u'Analyst', u'Creator', u'Date', ...]

    >>> sorted(cat.get("schema"))
    [u'Analyst', u'CreationDate', u'Creator',...]

    >>> sorted(cat.get("portal_types"))
    [u'ARReport', u'ARTemplate', u'ARTemplates',...]


Get a single catalog
~~~~~~~~~~~~~~~~~~~~

A single catalog can also be retrieved by it's id:

    >>> response = get("catalogs/portal_catalog")
    >>> cat = json.loads(response)
    >>> sorted(cat.get("indexes"))
    [u'Analyst', u'Creator', u'Date', ...]

    >>> sorted(cat.get("schema"))
    [u'Analyst', u'CreationDate', u'Creator',...]

    >>> sorted(cat.get("portal_types"))
    [u'ARReport', u'ARTemplate', u'ARTemplates',...]
