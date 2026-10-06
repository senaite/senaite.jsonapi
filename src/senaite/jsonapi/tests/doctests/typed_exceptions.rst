TYPED EXCEPTIONS
----------------

Coverage for `senaite.jsonapi.exceptions` — the typed subclasses of
`APIError` that back the JSON error envelope's `type` field.

Running this test from the buildout directory:

    bin/test test_doctests -t typed_exceptions


Test Setup
~~~~~~~~~~

    >>> import json
    >>> from base64 import b64encode
    >>> from plone.testing.zope import Browser
    >>> from senaite.jsonapi.exceptions import APIError
    >>> from senaite.jsonapi.exceptions import BadRequestError
    >>> from senaite.jsonapi.exceptions import ConflictError
    >>> from senaite.jsonapi.exceptions import ForbiddenError
    >>> from senaite.jsonapi.exceptions import NotFoundError
    >>> from senaite.jsonapi.exceptions import UnauthorizedError
    >>> from senaite.jsonapi.exceptions import ValidationError

Variables:

    >>> portal = self.portal
    >>> api_url = "{}/@@API/senaite/v1".format(portal.absolute_url())


Every typed exception subclasses APIError
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Anything that used to `except APIError` still catches every typed
subclass, so downstream code is not broken by the split.

    >>> issubclass(BadRequestError, APIError)
    True
    >>> issubclass(UnauthorizedError, APIError)
    True
    >>> issubclass(ForbiddenError, APIError)
    True
    >>> issubclass(NotFoundError, APIError)
    True
    >>> issubclass(ConflictError, APIError)
    True
    >>> issubclass(ValidationError, APIError)
    True


Each subclass carries the expected default HTTP status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> BadRequestError.status
    400
    >>> UnauthorizedError.status
    401
    >>> ForbiddenError.status
    403
    >>> NotFoundError.status
    404
    >>> ConflictError.status
    409
    >>> ValidationError.status
    422


Instantiating carries the message and the class-level status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The message survives str():

    >>> err = NotFoundError("no such widget")
    >>> str(err)
    'no such widget'
    >>> err.status
    404

An explicit `status=` overrides the class default (rarely useful, but
handy when the same class handles a family of related errors):

    >>> err = ForbiddenError("nope", status=451)
    >>> err.status
    451


APIError still accepts a status keyword for the legacy api.fail path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`api.fail(status, msg)` raises a plain APIError with a runtime-chosen
status; the class default is 500 when nothing else is specified:

    >>> APIError("boom").status
    500
    >>> APIError("boom", status=418).status
    418


Typed exceptions reach the HTTP client as the correct status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Anonymous callers hitting /registry raise UnauthorizedError from
api.check_permission, which sets HTTP 401 on the response:

    >>> anon = Browser(self.portal)
    >>> anon.handleErrors = False
    >>> anon.open("{}/registry".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

A non-Manager user hitting the same route raises ForbiddenError
(HTTP 403):

    >>> creds = b64encode("test_labclerk_0:test_labclerk_0")
    >>> clerk = Browser(self.portal)
    >>> clerk.handleErrors = False
    >>> clerk.addHeader("Authorization", "Basic {}".format(creds))
    >>> clerk.open("{}/registry".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 403: Forbidden

Asking for a resource that does not map to any portal type reaches
NotFoundError (HTTP 404):

    >>> clerk = Browser(self.portal)
    >>> clerk.handleErrors = False
    >>> clerk.addHeader("Authorization", "Basic {}".format(creds))
    >>> clerk.open("{}/no-such-resource".format(api_url))
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 404: Not Found
