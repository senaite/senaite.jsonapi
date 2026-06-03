DEXTERITY INHERITED FIELDS
--------------------------

Regression test for multi-schema Dexterity types.

When the searched object is a Dexterity (DX) type whose schema interface
inherits from another schema interface, the fields declared by the *parent*
schema must be returned too. The previous implementation relied on
``schema.names()``, which only returns the fields declared directly on the
interface (inherited fields require ``names(all=True)``), so inherited fields
were silently dropped from the API response.

``senaite.core.content.supplier.Supplier`` is a good example of a multi-schema
DX type: its schema ``ISupplierSchema`` inherits from ``IOrganizationSchema``.

Running this test from the buildout directory:

    bin/test test_doctests -t dexterity_inherited_fields


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import json
    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID

    >>> from bika.lims import api
    >>> from senaite.jsonapi import api as japi

Functional Helpers:

    >>> def get(url):
    ...     browser.open("{}/{}".format(api_url, url))
    ...     return browser.contents

Variables:

    >>> portal = self.portal
    >>> setup = portal.setup
    >>> portal_url = portal.absolute_url()
    >>> api_url = "{}/@@API/senaite/v1".format(portal_url)
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

Create a Supplier (DX type with an inherited schema):

    >>> supplier = api.create(setup.suppliers, "Supplier", Name="Naralabs")
    >>> uid = api.get_uid(supplier)
    >>> transaction.commit()


The DX type is genuinely multi-schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The schema interface inherits from a parent schema interface:

    >>> from senaite.core.content.supplier import ISupplierSchema
    >>> from senaite.core.content.organization import IOrganizationSchema
    >>> IOrganizationSchema in ISupplierSchema.__bases__
    True

``tax_number`` is declared by the *parent* ``IOrganizationSchema``, while
``lab_account_number`` is declared *directly* on ``ISupplierSchema``:

    >>> "tax_number" in IOrganizationSchema.names()
    True
    >>> "tax_number" in ISupplierSchema.names()
    False
    >>> "lab_account_number" in ISupplierSchema.names()
    True


Inherited fields are returned by get_fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fields mapping must contain both the directly declared field and the
inherited one:

    >>> fields = japi.get_fields(supplier)
    >>> "lab_account_number" in fields
    True
    >>> "tax_number" in fields
    True

``get_field`` resolves the inherited field too (it previously returned the
default because the field was missing from the mapping):

    >>> japi.get_field(supplier, "tax_number") is not None
    True


Inherited fields are present in the API response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

End to end, fetching the object exposes the inherited field as a key:

    >>> response = get(uid)
    >>> data = json.loads(response)
    >>> "lab_account_number" in data
    True
    >>> "tax_number" in data
    True
