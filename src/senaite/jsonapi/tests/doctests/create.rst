CREATE
------

Running this test from the buildout directory:

    bin/test test_doctests -t create


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from DateTime import DateTime
    >>> from operator import itemgetter
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

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, urllib.urlencode(data))
    ...     return browser.contents

    >>> def create(data):
    ...     response = post("create", data)
    ...     assert("items" in response)
    ...     response = json.loads(response)
    ...     items = response.get("items")
    ...     assert(len(items)==1)
    ...     item = response.get("items")[0]
    ...     assert("uid" in item)
    ...     return api.get_object(item["uid"])

    >>> def get_items(url, output):
    ...     output = json.loads(output)
    ...     return output.get("items")

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> setup = api.get_setup()
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


Create with resource
~~~~~~~~~~~~~~~~~~~~

Authenticate:

    >>> login()

We can create an object by providing the resource and the parent uid directly
in the request:

    >>> clients = portal.clients
    >>> clients_uid = api.get_uid(clients)
    >>> url = "client/create/{}".format(clients_uid)
    >>> data = {"title": "Test client 1",
    ...         "ClientID": "TC1"}
    >>> post(url, data)
    '{"count": 1, ..."url": ...clients/client-1", ...}'

We can also omit the parent uid while defining the resource, but passing the
uid of the container via post:

    >>> data = {"title": "Test client 2",
    ...         "ClientID": "TC2",
    ...         "parent_uid": clients_uid}
    >>> post("client/create", data)
    '{"count": 1, ..."url": ...clients/client-2", ...}'

We can use `parent_path` instead of `parent_uid`:

    >>> data = {"title": "Test client 3",
    ...         "ClientID": "TC3",
    ...         "parent_path": api.get_path(clients)}
    >>> post("client/create", data)
    '{"count": 1, ..."url": ...clients/client-3", ...}'


Create without resource
~~~~~~~~~~~~~~~~~~~~~~~

Or we can create an object without the resource, but with the parent uid and
defining the portal_type via post:

    >>> url = "create/{}".format(clients_uid)
    >>> data = {"title": "Test client 4",
    ...         "ClientID": "TC4",
    ...         "portal_type": "Client"}
    >>> post(url, data)
    '{"count": 1, ..."url": ...clients/client-4", ...}'


Create via post only
~~~~~~~~~~~~~~~~~~~~

We can omit both the resource and container uid and pass everything via post:

    >>> data = {"title": "Test client 5",
    ...         "ClientID": "TC5",
    ...         "portal_type": "Client",
    ...         "parent_path": api.get_path(clients)}
    >>> post("create", data)
    '{"count": 1, ..."url": ...clients/client-5", ...}'

    >>> data = {"title": "Test client 6",
    ...         "ClientID": "TC6",
    ...         "portal_type": "Client",
    ...         "parent_uid": clients_uid}
    >>> post("create", data)
    '{"count": 1, ..."url": ...clients/client-6", ...}'

If we do a search now for clients, we will get all them:

    >>> output = get("client")
    >>> output = json.loads(output)
    >>> items = output.get("items")
    >>> items = map(lambda it: it.get("getClientID"), items)
    >>> sorted(items)
    [u'TC1', u'TC2', u'TC3', u'TC4', u'TC5', u'TC6']


Create a Client
~~~~~~~~~~~~~~~

    >>> data = {"portal_type": "Client",
    ...         "parent_path": api.get_path(clients),
    ...         "title": "Omelette corp",
    ...         "ClientID": "EC"}
    >>> client = create(data)
    >>> client.getClientID()
    'EC'

Create a Client Contact
~~~~~~~~~~~~~~~~~~~~~~~

Client contact makes use of a `ICreate` adapter, cause it requires some
additional logic on creation

    >>> data = {"portal_type": "Contact",
    ...         "parent_path": api.get_path(client),
    ...         "Firstname": "Proud",
    ...         "Lastname": "Hen"}
    >>> contact = create(data)
    >>> contact.getFullname()
    'Proud Hen'

Creating a Sample
~~~~~~~~~~~~~~~~~

The creation of a Sample (`AnalysisRequest` portal type) is handled differently
from the rest of objects, an specific function in `senaite.core` must be used
instead of the plone's default creation.

Create some necessary objects first (by using `senaite.jsonapi`):

