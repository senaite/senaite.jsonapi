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

    >>> from Products.CMFPlone.interfaces.controlpanel import IMailSchema
    >>> result = api_settings.get_settings_from_interface(IMailSchema)

The outer key is the schema class name:

    >>> list(result.keys())
    ['IMailSchema']

Every value in the inner dict must be JSON-serializable — that is the
point of the helper's filter:

    >>> serialized = json.dumps(result)
    >>> "IMailSchema" in serialized
    True


get_registry_records_by_keyword filters by substring, case-insensitive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    >>> plone_records = api_settings.get_registry_records_by_keyword("plone")
    >>> isinstance(plone_records, dict)
    True
    >>> len(plone_records) > 0
    True
    >>> all(["plone" in name.lower() for name in plone_records])
    True

Passing None returns every record; the total strictly exceeds the
filtered subset:

    >>> total = api_settings.get_registry_records_by_keyword(None)
    >>> len(total) > len(plone_records)
    True


get_settings_by_keyword via the /settings route
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`get_settings_by_keyword` calls `api.url_for` which needs a live
request, so it is exercised through the HTTP route.

    >>> def as_manager():
    ...     b = Browser(self.portal)
    ...     b.addHeader("Accept-Language", "en-US")
    ...     b.handleErrors = False
    ...     creds = b64encode("{}:{}".format(TEST_USER_NAME, TEST_USER_PASSWORD))
    ...     b.addHeader("Authorization", "Basic {}".format(creds))
    ...     return b

    >>> b = as_manager()
    >>> b.open("{}/settings/mail".format(api_url))
    >>> data = json.loads(b.contents)
    >>> items = data["items"]
    >>> len(items)
    1
    >>> "mail" in items[0]
    True
    >>> items[0]["api_url"].endswith("/settings/mail")
    True



usergroups merges both mapped interfaces into a single section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`CONTROLPANEL_INTERFACE_MAPPING["usergroups"]` holds two interfaces
(`IUserGroupsSettingsSchema` + `ISecuritySchema`). Both must appear
as sub-keys under `"usergroups"`:

    >>> b = as_manager()
    >>> b.open("{}/settings/usergroups".format(api_url))
    >>> ug = json.loads(b.contents)["items"][0]["usergroups"]
    >>> sorted(k.encode("ascii") for k in ug.keys())
    ['ISecuritySchema', 'IUserGroupsSettingsSchema']
