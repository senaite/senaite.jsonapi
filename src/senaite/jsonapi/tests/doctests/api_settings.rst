API SETTINGS MODULE
-------------------

Direct-call coverage for `senaite.jsonapi.api.settings`. Complements
the HTTP-level tests in security_fixes.rst by exercising the extracted
helpers without going through the routes.

Running this test from the buildout directory:

    bin/test test_doctests -t api_settings


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
    >>> from senaite.jsonapi import api
    >>> from senaite.jsonapi.api import settings as api_settings


Variables:

    >>> portal = self.portal
    >>> api_url = "{}/@@API/senaite/v1".format(portal.absolute_url())
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()


Backward-compat surface
~~~~~~~~~~~~~~~~~~~~~~~

Every extracted name must remain importable from `senaite.jsonapi.api`
so add-ons and route code keep working after the split.

    >>> api.get_registry_records_by_keyword is (
    ...     api_settings.get_registry_records_by_keyword)
    True

    >>> api.get_settings_by_keyword is api_settings.get_settings_by_keyword
    True

    >>> api.get_settings_from_interface is (
    ...     api_settings.get_settings_from_interface)
    True

    >>> api.CONTROLPANEL_INTERFACE_MAPPING is (
    ...     api_settings.CONTROLPANEL_INTERFACE_MAPPING)
    True


CONTROLPANEL_INTERFACE_MAPPING covers the expected keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> sorted(api_settings.CONTROLPANEL_INTERFACE_MAPPING.keys())
    ['dateandtime', 'language', 'mail', 'maintenance', 'usergroups']


get_settings_from_interface returns {schema_name: {field: value}}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set known values on the mail control panel so we can assert them
end-to-end through the helper:

    >>> from plone import api as ploneapi
    >>> from Products.CMFPlone.interfaces.controlpanel import IMailSchema
    >>> from zope.component import getAdapter
    >>> mail = getAdapter(portal, IMailSchema)
    >>> mail.smtp_host = u"mail.example.com"
    >>> mail.smtp_port = 2525
    >>> mail.email_from_name = u"SENAITE Lab"
    >>> mail.email_from_address = "lab@example.com"
    >>> transaction.commit()

    >>> result = api_settings.get_settings_from_interface(IMailSchema)

The outer key is the schema class name:

    >>> list(result.keys())
    ['IMailSchema']

The values we just wrote come back verbatim:

    >>> fields = result["IMailSchema"]
    >>> fields["smtp_host"]
    u'mail.example.com'
    >>> fields["smtp_port"]
    2525
    >>> fields["email_from_name"]
    u'SENAITE Lab'
    >>> fields["email_from_address"]
    'lab@example.com'

The whole dict must be JSON-serializable — that is the point of the
helper's filter:

    >>> "mail.example.com" in json.dumps(result)
    True


get_registry_records_by_keyword filters by substring, case-insensitive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The mail schema fields also land in the portal registry, so setting
them above gave us a known key/value pair to look up here. Filtering
by `smtp_host` returns the record with our stored value:

    >>> hits = api_settings.get_registry_records_by_keyword("smtp_host")
    >>> "plone.smtp_host" in hits
    True
    >>> hits["plone.smtp_host"]
    u'mail.example.com'

The filter is case-insensitive:

    >>> upper = api_settings.get_registry_records_by_keyword("SMTP_HOST")
    >>> upper == hits
    True

A keyword that matches nothing returns an empty dict:

    >>> api_settings.get_registry_records_by_keyword(
    ...     "no-such-registry-key")
    {}

Passing None returns every record; the total strictly exceeds any
filtered subset:

    >>> total = api_settings.get_registry_records_by_keyword(None)
    >>> len(total) > len(hits)
    True


Non JSON serializable values are coerced
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some registry records hold `datetime` values, which the JSON encoder used
by the route cannot serialize. Such values are coerced to ISO strings:

    >>> from datetime import datetime
    >>> from plone.registry import field
    >>> from plone.registry.record import Record
    >>> reg = ploneapi.portal.get_tool("portal_registry")
    >>> reg.records["senaite.jsonapi.test_datetime"] = Record(
    ...     field.Datetime(title=u"Test"),
    ...     datetime(2014, 8, 14, 0, 0, 0, 3))
    >>> transaction.commit()

    >>> hits = api_settings.get_registry_records_by_keyword("test_datetime")
    >>> hits["senaite.jsonapi.test_datetime"]
    '2014-08-14T00:00:00.000003'

So the whole record set is now JSON serializable:

    >>> ignored = json.dumps(
    ...     api_settings.get_registry_records_by_keyword(None))


get_settings_by_keyword via the /settings route
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`get_settings_by_keyword` calls `api.url_for` which needs a live
request, so it is exercised through the HTTP route. The cookie-login
browser is used instead of Basic auth because the fixture's Basic-auth
path for TEST_USER_NAME is not reliable across every CI build.

    >>> b = self.getBrowser()
    >>> b.open("{}/settings/mail".format(api_url))
    >>> data = json.loads(b.contents)
    >>> items = data["items"]
    >>> len(items)
    1
    >>> "mail" in items[0]
    True
    >>> items[0]["api_url"].endswith("/settings/mail")
    True

The values we set above flow all the way through the route:

    >>> mail_section = items[0]["mail"]["IMailSchema"]
    >>> mail_section["smtp_host"]
    u'mail.example.com'
    >>> mail_section["email_from_address"]
    u'lab@example.com'



usergroups merges both mapped interfaces into a single section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`CONTROLPANEL_INTERFACE_MAPPING["usergroups"]` holds two interfaces
(`IUserGroupsSettingsSchema` + `ISecuritySchema`). Both must appear
as sub-keys under `"usergroups"`:

    >>> b = self.getBrowser()
    >>> b.open("{}/settings/usergroups".format(api_url))
    >>> ug = json.loads(b.contents)["items"][0]["usergroups"]
    >>> sorted(k.encode("ascii") for k in ug.keys())
    ['ISecuritySchema', 'IUserGroupsSettingsSchema']
