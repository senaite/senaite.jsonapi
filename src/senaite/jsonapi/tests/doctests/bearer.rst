BEARER TOKEN AUTHENTICATION
---------------------------

Running this test from the buildout directory:

    bin/test test_doctests -t bearer


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
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

    >>> def with_bearer(b, token):
    ...     b.addHeader("Authorization", "Bearer {}".format(token))
    ...     return b

    >>> def is_authenticated(b):
    ...     b.open("{}/users/current".format(api_url))
    ...     return json.loads(b.contents)["items"][0]["authenticated"]


Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


No token, no authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A fresh browser without any credentials is anonymous:

    >>> is_authenticated(fresh_browser())
    False


A valid Bearer token authenticates the request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Issue a token for the test user (this is what /login does internally
once the user is authenticated):

    >>> token = create_token(TEST_USER_ID)
    >>> transaction.commit()
    >>> isinstance(token, basestring) and len(token) > 0
    True

A fresh browser carrying that token in the `Authorization: Bearer`
header is authenticated by the JWT PAS plugin:

    >>> is_authenticated(with_bearer(fresh_browser(), token))
    True


The X-JWT-Auth-Token fallback header authenticates the request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients that cannot set the `Authorization` header (some embedded
HTTP libraries, browser extensions, etc.) can use the
`X-JWT-Auth-Token` fallback header instead:

    >>> fallback = fresh_browser()
    >>> fallback.addHeader("X-JWT-Auth-Token", token.encode("ascii"))
    >>> is_authenticated(fallback)
    True


An invalid Bearer token does not authenticate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A garbage value cannot be decoded, so the request stays anonymous:

    >>> is_authenticated(with_bearer(fresh_browser(), "not-a-real-token"))
    False


A token signed with the wrong secret does not authenticate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A well-formed JWT signed with a different secret fails signature
verification:

    >>> import jwt as pyjwt
    >>> forged = pyjwt.encode(
    ...     {"userid": TEST_USER_ID, "exp": timestamp(seconds=3600)},
    ...     "wrong-secret", algorithm="HS256")
    >>> is_authenticated(with_bearer(fresh_browser(), forged))
    False


A token for an unknown user does not create a keystorage entry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tokens that claim to belong to a user who does not exist must be
rejected without touching the per-user keystorage. Otherwise an
anonymous attacker can force unbounded ZODB writes by spraying
tokens with random userids.

    >>> from senaite.jsonapi.pas.plugin import get_keystorage
    >>> before = set(get_keystorage().keys())

    >>> attacker = pyjwt.encode(
    ...     {"userid": "nobody-12345", "exp": timestamp(seconds=3600)},
    ...     "attacker-secret", algorithm="HS256")
    >>> is_authenticated(with_bearer(fresh_browser(), attacker))
    False

    >>> set(get_keystorage().keys()) == before
    True


An expired token does not authenticate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A token whose `exp` claim lies in the past is rejected by PyJWT:

    >>> expired_token = create_token(TEST_USER_ID, exp=timestamp(seconds=-60))
    >>> transaction.commit()
    >>> is_authenticated(with_bearer(fresh_browser(), expired_token))
    False


Rotating the user's secret revokes existing tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After `rotate_secret`, the previously-issued token no longer
verifies:

    >>> rotate_secret(TEST_USER_ID)
    >>> transaction.commit()
    >>> is_authenticated(with_bearer(fresh_browser(), token))
    False

A token issued after the rotation is accepted again:

    >>> new_token = create_token(TEST_USER_ID)
    >>> transaction.commit()
    >>> is_authenticated(with_bearer(fresh_browser(), new_token))
    True
