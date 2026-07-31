REST VERBS (PUT / PATCH / DELETE)
---------------------------------

The object-addressed action route accepts the REST verbs in addition to
POST: PUT and PATCH map to `update`, DELETE maps to `delete`. This lets
REST-native clients use the natural HTTP method instead of the
`X-HTTP-Method-Override` header or an explicit action segment in the URL.

Running this test from the buildout directory:

    bin/test test_doctests -t rest_verbs


Test Setup
~~~~~~~~~~

    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from bika.lims import api

Functional Helpers:

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, urllib.urlencode(data, doseq=True))
    ...     return browser.contents

    >>> def get_item_object(response):
    ...     response = json.loads(response)
    ...     item = response.get("items")[0]
    ...     return api.get_object(item["uid"])

    >>> def create(data):
    ...     return get_item_object(post("create", data))

The verbs are issued through the browser's underlying WebTest app,
which supports arbitrary HTTP methods and shares the logged-in cookie
jar. Data is form-encoded, matching the POST helper above; the update
route merges the form into the request record.

    >>> def send(method, path, data=None):
    ...     url = "{}/{}".format(api_url, path)
    ...     verb = getattr(browser.testapp, method.lower())
    ...     if data is None:
    ...         return verb(url, expect_errors=True)
    ...     return verb(url, data, expect_errors=True)

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Create two clients to work on:

    >>> clients = api.get_portal().clients
    >>> c1 = create({"portal_type": "Client",
    ...              "parent_path": api.get_path(clients),
    ...              "title": "Verb Corp", "ClientID": "VC"})
    >>> c2 = create({"portal_type": "Client",
    ...              "parent_path": api.get_path(clients),
    ...              "title": "Doomed Corp", "ClientID": "DC"})
    >>> c1_uid = api.get_uid(c1)
    >>> c2_uid = api.get_uid(c2)


PATCH updates the object
~~~~~~~~~~~~~~~~~~~~~~~~

A PATCH to the object's UID with no action segment is dispatched to
`update`:

    >>> resp = send("PATCH", c1_uid, {"title": "Patched Corp"})
    >>> resp.status_int
    200
    >>> data = json.loads(resp.body)
    >>> data["items"][0]["title"]
    u'Patched Corp'

The change is persisted:

    >>> transaction.commit()
    >>> api.get_object(c1_uid).Title()
    'Patched Corp'


PUT updates the object
~~~~~~~~~~~~~~~~~~~~~~

PUT behaves the same as PATCH (both map to `update`):

    >>> resp = send("PUT", c1_uid, {"title": "Put Corp"})
    >>> resp.status_int
    200
    >>> json.loads(resp.body)["items"][0]["title"]
    u'Put Corp'


DELETE deactivates the object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A DELETE to the object's UID is dispatched to `delete`, which
deactivates the object (SENAITE never hard-deletes):

    >>> resp = send("DELETE", c2_uid)
    >>> resp.status_int
    200
    >>> data = json.loads(resp.body)
    >>> data["count"]
    1

The object still exists but is now inactive:

    >>> api.get_review_status(api.get_object(c2_uid))
    'inactive'


GET is unaffected
~~~~~~~~~~~~~~~~~

The verb routing does not disturb the existing GET route:

    >>> resp = send("GET", c1_uid)
    >>> resp.status_int
    200
    >>> json.loads(resp.body)["title"]
    u'Put Corp'


POST without an action or override is still an error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The historic POST behaviour is preserved: a bare POST to a UID with no
action segment and no override header cannot resolve an action:

    >>> resp = send("POST", c1_uid, {"title": "ignored"})
    >>> resp.status_int
    400
    >>> "None_items" in json.loads(resp.body)["message"]
    True
