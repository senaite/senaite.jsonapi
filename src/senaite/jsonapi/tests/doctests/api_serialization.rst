API SERIALIZATION MODULE
------------------------

Direct-call coverage for `senaite.jsonapi.api.serialization`. The
HTTP-level doctests (read, create, search) already exercise these
helpers through the routes; this file pins the module surface itself
so refactors don't silently change return shapes or drop backward-
compat re-exports.

Running this test from the buildout directory:

    bin/test test_doctests -t api_serialization


Test Setup
~~~~~~~~~~

    >>> import json
    >>> import transaction
    >>> from bika.lims import api as bika_api
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from senaite.jsonapi import api
    >>> from senaite.jsonapi.api import serialization as api_ser

Fixture context:

    >>> portal = self.portal
    >>> api_url = "{}/@@API/senaite/v1".format(portal.absolute_url())
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


Backward-compat surface
~~~~~~~~~~~~~~~~~~~~~~~

Every extracted name must remain importable from `senaite.jsonapi.api`
so fieldmanagers.py (api.get_file_info, api.get_url_info) and any
downstream users keep working after the split.

    >>> api.get_info is api_ser.get_info
    True

    >>> api.get_url_info is api_ser.get_url_info
    True

    >>> api.get_parent_info is api_ser.get_parent_info
    True

    >>> api.get_children_info is api_ser.get_children_info
    True

    >>> api.get_file_info is api_ser.get_file_info
    True

    >>> api.get_workflow_info is api_ser.get_workflow_info
    True


get_parent_info returns {} for the portal root
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The portal has no parent to describe, so the helper short-circuits to
an empty dict without touching url_for:

    >>> api_ser.get_parent_info(portal)
    {}


get_workflow_info describes the assigned workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a Client (has the bika_client_workflow) and read back its
workflow shape:

    >>> client = bika_api.create(
    ...     portal.clients, "Client", title="Acme", ClientID="AC")
    >>> transaction.commit()

    >>> wf = api_ser.get_workflow_info(client)
    >>> "workflow_info" in wf
    True

    >>> entry = wf["workflow_info"][0]
    >>> sorted(entry.keys())
    ['review_history', 'review_state', 'status', 'transitions', 'workflow']

The initial review_state for a fresh Client is `active`:

    >>> entry["review_state"]
    'active'

Transitions carry a plain dict shape usable by generic UIs:

    >>> transitions = entry["transitions"]
    >>> len(transitions) > 0
    True
    >>> sorted(transitions[0].keys())
    ['display', 'title', 'url', 'value']

An object without any assigned workflow returns an empty list rather
than raising:

    >>> api_ser.get_workflow_info(portal)
    []


get_url_info, get_parent_info and get_info via the /read HTTP route
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These three helpers call `api.url_for`, which needs a live request.
Exercise them through the /read route which drives the full get_info
pipeline (url_info + parent_info + IInfo adapters):

    >>> browser = self.getBrowser()
    >>> uid = bika_api.get_uid(client)
    >>> browser.open("{}/client/{}".format(api_url, uid))
    >>> data = json.loads(browser.contents)
    >>> item = data["items"][0]

The url_info keys are present:

    >>> "uid" in item and "url" in item and "api_url" in item
    True

    >>> item["uid"] == uid
    True

    >>> item["url"] == client.absolute_url()
    True

    >>> item["api_url"].endswith("/client/{}".format(uid))
    True

The parent_info keys are present and point at the clients folder:

    >>> item["parent_id"]
    u'clients'

    >>> item["parent_uid"] == bika_api.get_uid(portal.clients)
    True

    >>> item["parent_url"].endswith("/{}".format(item["parent_uid"]))
    True


get_info with `?complete=yes` adds the snapshot version and workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `version` key only appears in the complete response, because it
requires waking up the full content object. Same for the workflow
block, which additionally needs `?workflow=yes`:

    >>> browser.open(
    ...     "{}/client/{}?complete=yes&workflow=yes".format(api_url, uid))
    >>> item = json.loads(browser.contents)["items"][0]

    >>> "version" in item
    True
    >>> isinstance(item["version"], int)
    True

    >>> "workflow_info" in item
    True
    >>> item["workflow_info"][0]["review_state"]
    u'active'
