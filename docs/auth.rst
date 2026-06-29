Authentication
==============

The API provides a simple way to authenticate a user with SENAITE.


Login
-----

:URL Schema: ``<BASE URL>/login?__ac_name=<username>&__ac_password=<password>``

The response sets the ``__ac`` cookie for further cookie-authenticated
requests. In addition, a JSON Web Token (JWT) is returned in the
response body as ``token`` (with the Unix expiration timestamp as
``expires``) and is also set as the HttpOnly ``token`` cookie.
Subsequent requests can be authenticated with either the cookie or by
sending the token in the ``Authorization: Bearer <token>`` header (see
``Bearer Token Authentication`` below).

The route accepts two authentication modes:

1. **HTTP Basic auth** (``Authorization: Basic ...`` header). No body
   fields are needed; the route issues a token for the user that was
   already authenticated by the PAS layer.
2. **Form login** with ``__ac_name`` and ``__ac_password`` as form
   fields, as shown in the example below.

Example

``http://localhost:8080/senaite/@@API/senaite/v1/login?__ac_name=admin&__ac_password=admin``

Response

.. code-block:: javascript

    {
        url: "http://localhost:8080/senaite/@@API/senaite/v1/users",
        count: 1,
        token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        expires: 1735689600,
        _runtime: 0.0019960403442382812,
        items: [
            {
                username: "admin",
                authenticated: true,
                last_login_time: "",
                roles: [
                    "Manager",
                    "Authenticated"
                ],
                url: "http://localhost:8080/senaite/@@API/senaite/v1/users/admin",
                email: null,
                groups: [ ],
                fullname: null,
                id: "admin",
                login_time: ""
            }
        ]
    }


Logout
------

:URL Schema: ``<BASE URL>/users/logout``

The response expires the ``__ac`` and ``token`` cookies on the client.
Note that this does not invalidate the JWT itself: a token that was
already extracted from the response and stored by the client remains
valid until its ``exp`` claim is reached. To revoke a token
server-side before it expires, rotate the user's signing secret with
``senaite.jsonapi.pas.plugin.rotate_secret(userid)``; this invalidates
every token previously issued for that user.

Example

``http://localhost:8080/senaite/@@API/senaite/v1/users/logout``

Response

.. code-block:: javascript

    {
        url: "http://localhost:8080/senaite/@@API/senaite/v1/users",
        _runtime: 0.0009028911590576172,
        success: true
    }


Basic Authentication
--------------------

:URL Schema: ``<BASE URL>/auth``

If the request is not authenticated, this route will raise an unauthorized
response with status code 401. Browsers should display the Basic Authentication
login.

Example

``http://localhost:8080/senaite/@@API/senaite/v1/auth``


Bearer Token Authentication
---------------------------

After a successful ``/login`` call, the JWT returned in the response
body can be used to authenticate any subsequent request by sending it
in the standard ``Authorization`` header:

.. code-block:: text

    Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

The token is extracted, in this order, from:

1. ``Authorization: Bearer <token>`` header
2. ``token`` cookie (HttpOnly, set automatically by ``/login``)
3. ``X-JWT-Auth-Token`` header (fallback for clients that cannot set
   the ``Authorization`` header)

Tokens are signed per user with a secret generated on first use and
stored in the portal's annotations. The default token lifetime is
60 minutes (``JWT_TOKENS_TIMEOUT`` in ``senaite.jsonapi.config``).

Example

.. code-block:: bash

    curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8080/senaite/@@API/senaite/v1/users/current


Revoking tokens
~~~~~~~~~~~~~~~

JWTs are stateless: ``/logout`` only expires the client-side cookie. To
revoke every token issued for a given user, rotate their signing
secret from a debug shell or upgrade step:

.. code-block:: python

    from senaite.jsonapi.pas.plugin import rotate_secret
    rotate_secret("johndoe")

The next call to ``/login`` for that user generates a new secret and
issues a new token; all previously-issued tokens fail signature
verification.


Cookie security
~~~~~~~~~~~~~~~

The ``token`` cookie is set with ``HttpOnly``, ``Secure`` and
``SameSite=Lax``. The ``Secure`` flag means the cookie is only sent
over HTTPS; on plain HTTP setups (local development, non-TLS
deployments) the cookie will not round-trip and clients must use the
``Authorization: Bearer`` header instead.
