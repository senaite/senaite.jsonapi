USERS
-----

Running this test from the buildout directory:

    bin/test test_doctests -t users


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

Get all users
~~~~~~~~~~~~~

The API is capable to find SENAITE users:

    >>> response = get("users")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> sorted(map(lambda it: it["username"], items))
    [u'test-user', u'test_analyst_0',...u'test_labmanager_1']

And for each user, the roles and groups are displayed:

    >>> analyst = filter(lambda it: it["username"] == "test_analyst_0", items)[0]
    >>> sorted(analyst.get("roles"))
    [u'Analyst', u'Authenticated', u'Member']

    >>> sorted(analyst.get("groups"))
    [u'Analysts', u'AuthenticatedUsers']

As well as other properties:

    >>> sorted(analyst.keys())
    [u'api_url', u'authenticated', u'description', u'email', ...]

Get current user
~~~~~~~~~~~~~~~~

Current user can also be retrieved easily:

    >>> response = get("users/current")
    >>> data = json.loads(response)
    >>> data.get("count")
    1
    >>> current = data.get("items")[0]
    >>> current.get("username")
    u'test-user'

and includes all properties too:

    >>> sorted(current.keys())
    [u'api_url', u'authenticated', u'description', u'email',...u'groups',...u'roles'...]

Get a single user
~~~~~~~~~~~~~~~~~

A single user can be retrieved too:

    >>> get("users/test_analyst_0")
    '..."username": "test_analyst_0"...'
