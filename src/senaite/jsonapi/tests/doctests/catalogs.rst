CATALOGS
--------

Running this test from the buildout directory:

    bin/test test_doctests -t catalogs


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

Functional Helpers:

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents


Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
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
    [u'portal_catalog', ...]

Catalogs for internal use are not included though:

    >>> "uid_catalog" in catalog_ids
    False

    >>> "reference_catalog" in catalog_ids
    False

For each catalog, indexes, schema fields and allowed portal types are listed:

    >>> cat = filter(lambda it: it["id"]=="senaite_catalog_analysis", items)[0]
    >>> sorted(cat.get("indexes"))
    [...]

    >>> sorted(cat.get("schema"))
    [...]

    >>> sorted(cat.get("portal_types"))
    [u'Analysis', u'DuplicateAnalysis', u'ReferenceAnalysis', u'RejectAnalysis']


Get a single catalog
~~~~~~~~~~~~~~~~~~~~

A single catalog can also be retrieved by it's id:

    >>> response = get("catalogs/senaite_catalog_analysis")
    >>> cat = json.loads(response)
    >>> sorted(cat.get("indexes"))
    [...]

    >>> sorted(cat.get("schema"))
    [...]

    >>> sorted(cat.get("portal_types"))
    [u'Analysis', u'DuplicateAnalysis', u'ReferenceAnalysis', u'RejectAnalysis']
