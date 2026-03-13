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
    [u'api_url', u'authenticated', u'email', ...]

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
    [u'api_url', u'authenticated', u'email',...u'groups',...u'roles'...]

Get a single user
~~~~~~~~~~~~~~~~~

A single user can be retrieved too:

    >>> get("users/test_analyst_0")
    '..."username": "test_analyst_0"...'

Extend user info via IInfo
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can enrich the user payload by registering an `IInfo` adapter for the
Plone user. This adapter’s `to_dict` will be merged into each user item.

Create and register a dummy `IInfo` adapter, following the pattern used in the
push doctest:

    >>> from senaite.jsonapi.interfaces import IInfo, IUsersFilter
    >>> from zope.component import getGlobalSiteManager
    >>> from zope.interface import implements
    >>> from Products.PluggableAuthService.interfaces.authservice import IPropertiedUser
    >>> from zope.publisher.interfaces.browser import IBrowserRequest
    >>> from senaite.jsonapi import request as req

    >>> True = (1 == 1)
    >>> False = (1 == 0)

    >>> class DummyUserInfoAdapter(object):
    ...     """Adds a dummy flag to user info"""
    ...     implements(IInfo)
    ...     def __init__(self, context):
    ...         self.context = context
    ...     def to_dict(self):
    ...         return {"dummy_info": True}

    >>> sm = getGlobalSiteManager()
    >>> sm.registerAdapter(DummyUserInfoAdapter, (IPropertiedUser,), IInfo)
    >>> transaction.commit()

The current user info now includes the additional data:

    >>> response = get("users/current")
    >>> data = json.loads(response)
    >>> current = data.get("items")[0]
    >>> current.get("dummy_info")
    True

Filter users via IUsersFilter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The users listing (`/users`) can be filtered by request-scoped adapters that
implement `IUsersFilter`. Each adapter receives the current list of user ids
and returns a possibly filtered list. This filter is only applied to listings
and not when a specific username is requested.

Create and register a dummy filter that narrows the list when the querystring
contains `role=<rolename>`:

    >>> from senaite.jsonapi import api
    >>> class DummyUsersFilterAdapter(object):
    ...     """Filters users by the 'role' query param"""
    ...     implements(IUsersFilter)
    ...     def __init__(self, request):
    ...         self.request = request
    ...
    ...     def filter(self, user_ids):
    ...         role = req.get("role", None)
    ...         if not role:
    ...             return user_ids
    ...         filtered = []
    ...         for uid in user_ids:
    ...             user = api.get_user(uid)
    ...             if user and role in user.getRoles():
    ...                 filtered.append(uid)
    ...         return filtered

    >>> sm.registerAdapter(DummyUsersFilterAdapter, (IBrowserRequest,), IUsersFilter, name="dummy")
    >>> transaction.commit()

Requesting the users list with the filter applied returns only users with the
requested role:

    >>> response = get("users?role=Analyst")
    >>> data = json.loads(response)
    >>> items = data.get("items")
    >>> len(items) > 0
    True
    >>> all(map(lambda it: u'Analyst' in it.get('roles', []), items))
    True
