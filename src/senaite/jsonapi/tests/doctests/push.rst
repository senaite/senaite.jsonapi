PUSH
----

Running this test from the buildout directory:

    bin/test test_doctests -t push

Test Setup
----------

Needed Imports:

    >>> import json
    >>> import transaction
    >>> import urllib
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from senaite.jsonapi.interfaces import IPushConsumer
    >>> from zope.component import getGlobalSiteManager
    >>> from zope.interface import implements

Functional Helpers:

    >>> def post(url, data):
    ...     url = "{}/{}".format(api_url, url)
    ...     browser.post(url, urllib.urlencode(data, doseq=True))
    ...     return browser.contents

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Create a dummy `IPushConsumer` adapter:

    >>> class DummyConsumerAdapter(object):
    ...     implements(IPushConsumer)
    ...
    ...     def __init__(self, record):
    ...         self.record = record
    ...
    ...     def process(self):
    ...         if not self.record.get("target"):
    ...             return False
    ...         return True

    >>> sm = getGlobalSiteManager()
    >>> sm.registerAdapter(DummyConsumerAdapter, (dict,), IPushConsumer, name="dummy")
    >>> transaction.commit()


Push with success
~~~~~~~~~~~~~~~~~

    >>> post("push", {"consumer": "dummy", "target": "defined"})
    '..."success": true...'


Push without success
~~~~~~~~~~~~~~~~~~~~

If an adapter is registered, but it rises an exception, the outcome is failed:

    >>> post("push", {"consumer": "dummy"})
    '..."success": false...'


Non-registered adapter
~~~~~~~~~~~~~~~~~~~~~~

    >>> post("push", {"consumer": "zummy"})
    Traceback (most recent call last):
    [...]
    HTTPError: HTTP Error 500: Internal Server Error
