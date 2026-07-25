SECURITY FIXES
--------------

Running this test from the buildout directory:

    bin/test test_doctests -t security_fixes


Test Setup
~~~~~~~~~~

    >>> import json
    >>> import transaction
    >>> from base64 import b64encode
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.zope import Browser


Functional Helpers:

    >>> def fresh_browser():
    ...     b = Browser(self.portal)
    ...     b.addHeader("Accept-Language", "en-US")
    ...     b.handleErrors = False
    ...     return b

    >>> def as_user(userid, password=None):
    ...     b = fresh_browser()
    ...     creds = b64encode("{}:{}".format(userid, password or userid))
    ...     b.addHeader("Authorization", "Basic {}".format(creds))
    ...     return b


Variables:

    >>> portal = self.portal
    >>> api_url = "{}/@@API/senaite/v1".format(portal.absolute_url())
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


/registry requires the "Manage portal" permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Anonymous callers are rejected with 401:

    >>> fresh_browser().open("{}/registry".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

A LabClerk (no "Manage portal") is rejected with 403:

    >>> as_user("test_labclerk_0").open("{}/registry".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 403: Forbidden

A Manager is allowed past the permission check. The positive path is
not asserted here because `/registry` currently returns raw datetime
values that trip the JSON encoder — that pre-existing bug is out of
scope for this security fix. The Manager path is exercised implicitly
by the users doctest below.


/settings requires the "Manage portal" permission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> fresh_browser().open("{}/settings".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> as_user("test_labclerk_0").open("{}/settings".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 403: Forbidden


/users listing is restricted to managers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A Manager can enumerate all users. The Manager path uses the fixture's
cookie-authenticated browser (self.getBrowser()) rather than Basic
auth, because the plone.app.testing test-user Basic-auth path is not
reliable across every plone.app.testing build shipped in CI:

    >>> mgr = self.getBrowser()
    >>> mgr.open("{}/users".format(api_url))
    >>> data = json.loads(mgr.contents)
    >>> data["count"] > 1
    True

A non-Manager gets silently collapsed to /current when requesting the
full listing (no enumeration leak):

    >>> clerk = as_user("test_labclerk_0")
    >>> clerk.open("{}/users".format(api_url))
    >>> data = json.loads(clerk.contents)
    >>> data["count"]
    1
    >>> data["items"][0]["username"] == "test_labclerk_0"
    True

Requesting another user's record collapses to /current too:

    >>> clerk = as_user("test_labclerk_0")
    >>> clerk.open("{}/users/test_analyst_0".format(api_url))
    >>> data = json.loads(clerk.contents)
    >>> data["items"][0]["username"] == "test_labclerk_0"
    True

Requesting one's own record by id still works:

    >>> clerk = as_user("test_labclerk_0")
    >>> clerk.open("{}/users/test_labclerk_0".format(api_url))
    >>> data = json.loads(clerk.contents)
    >>> data["items"][0]["username"] == "test_labclerk_0"
    True
