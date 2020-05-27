AUTH
----

Running this test from the buildout directory:

    bin/test test_doctests -t auth


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

    >>> from bika.lims import api

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

Login
~~~~~

User can login with a GET:

    >>> get("login?__ac_name={}&__ac_password={}".format(TEST_USER_ID, TEST_USER_PASSWORD))
    '..."authenticated": true...'

And once logged, `auth` route does not rise an unauthorized response 401:

    >>> get("auth")
    '{"_runtime": ...}'

Logout
~~~~~~

User can logout easily too:

    >>> get("users/logout")
    '..."authenticated": false...'

And `auth` route rises an unauthorized response 401:

    >>> get("auth")
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 401: Unauthorized
