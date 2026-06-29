JWT LOGIN
---------

Running this test from the buildout directory:

    bin/test test_doctests -t login


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from base64 import b64encode
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.zope import Browser
    >>> from senaite.jsonapi.pas.plugin import create_token
    >>> from senaite.jsonapi.pas.plugin import rotate_secret
    >>> from senaite.jsonapi.pas.plugin import timestamp


Functional Helpers:

    >>> def fresh_browser():
    ...     b = Browser(self.portal)
    ...     b.addHeader("Accept-Language", "en-US")
    ...     b.handleErrors = False
    ...     return b

    >>> def basic(b, userid, password):
    ...     b.addHeader(
    ...         "Authorization", "Basic {}:{}".format(userid, password))
    ...     return b


Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


Issue a token via /login
~~~~~~~~~~~~~~~~~~~~~~~~

An already-authenticated user calls /login and obtains a JWT in the
response body. The setup helper ``self.getBrowser()`` returns a browser
that has a Plone session cookie, so the request is authenticated by
the cookie auth plugin before the route runs:

    >>> browser = self.getBrowser()
    >>> browser.open("{}/login".format(api_url))
    >>> data = json.loads(browser.contents)
    >>> data["items"][0]["authenticated"]
    True

    >>> token = data["token"]
    >>> isinstance(token, basestring) and len(token) > 0
    True

    >>> data["expires"] > timestamp()
    True

The response also sets the JWT as an HttpOnly, Secure cookie. The
test browser drives the API over plain HTTP, so the Secure cookie is
not retained by ``browser.cookies``; the assertion below would only
hold over HTTPS. Clients running on HTTP must therefore use the
``Authorization: Bearer`` header (covered next).


Authenticate with Authorization: Bearer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fresh browser (no Plone cookie, no Basic auth) authenticated only
with the Bearer token can access the auth-protected route:

    >>> bearer = fresh_browser()
    >>> bearer.addHeader("Authorization", "Bearer {}".format(token))
    >>> bearer.open("{}/auth".format(api_url))
    >>> "_runtime" in bearer.contents
    True

And `/users/current` returns the authenticated user:

    >>> bearer.open("{}/users/current".format(api_url))
    >>> info = json.loads(bearer.contents)
    >>> info["items"][0]["authenticated"]
    True


An invalid Bearer token is rejected
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A bogus token must not authenticate the request:

    >>> bogus = fresh_browser()
    >>> bogus.addHeader("Authorization", "Bearer not-a-real-token")
    >>> bogus.open("{}/auth".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized


An expired token is rejected
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A token that has already expired is treated as anonymous and rejected
by the auth route:

    >>> expired_token = create_token(TEST_USER_ID, exp=timestamp(seconds=-60))
    >>> transaction.commit()
    >>> expired = fresh_browser()
    >>> expired.addHeader("Authorization", "Bearer {}".format(expired_token))
    >>> expired.open("{}/auth".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized


Rotating the user's secret revokes existing tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After rotating, the previously-issued token no longer verifies:

    >>> rotate_secret(TEST_USER_ID)
    >>> transaction.commit()

    >>> revoked = fresh_browser()
    >>> revoked.addHeader("Authorization", "Bearer {}".format(token))
    >>> revoked.open("{}/auth".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

A freshly issued token works again:

    >>> new_token = create_token(TEST_USER_ID)
    >>> transaction.commit()
    >>> renewed = fresh_browser()
    >>> renewed.addHeader("Authorization", "Bearer {}".format(new_token))
    >>> renewed.open("{}/auth".format(api_url))
    >>> "_runtime" in renewed.contents
    True
