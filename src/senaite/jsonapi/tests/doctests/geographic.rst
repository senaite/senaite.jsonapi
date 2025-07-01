GEOGRAPHIC
----------------

Running this test from the buildout directory:

    bin/test test_doctests -t geographic


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

Functional Helpers:

    >>> def logout():
    ...     browser.open(portal_url + "/logout")
    ...     assert("You are now logged out" in browser.contents)

Variables:

    >>> portal = self.portal
    >>> portal_url = portal.absolute_url()
    >>> browser = self.getBrowser()
    >>> setRoles(portal, TEST_USER_ID, ["LabManager", "Manager"])
    >>> transaction.commit()

JSON API:

    >>> api_base_url = portal_url + "/@@API/senaite/v1"


Get all subdivisions
~~~~~~~~~~~~~~~~~~~~

The geo_subdivisions route should return all subdivisions at all depths when no
country is provided:

    >>> browser.open(api_base_url + "/geographic/subdivisions_schema")
    >>> import json
    >>> response = json.loads(browser.contents)
    >>> response["count"] > 0
    True
    >>> "items" in response
    True
    >>> len(response["items"]) > 0
    True
    >>> "name" in response["items"][0]
    True
    >>> "code" in response["items"][0]
    True
    >>> "type" in response["items"][0]
    True
    >>> "country_code" in response["items"][0]
    True
    >>> "parent_code" in response["items"][0]
    True
    >>> "parent" in response["items"][0]
    True
    >>> "depth" in response["items"][0]
    True
    >>> depths = set(item["depth"] for item in response["items"])
    >>> 1 in depths
    True
    >>> 2 in depths
    True


Get subdivisions for a specific country
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The geo_subdivisions route should return subdivisions for a specific country
when country is provided:

    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES")
    >>> response = json.loads(browser.contents)
    >>> response["count"] > 0
    True
    >>> response["country"] == "ES"
    True
    >>> response["depth"] == 0
    True
    >>> all(item["country_code"] == "ES" for item in response["items"])
    True
    >>> "parent" in response["items"][0]
    True


Get subdivisions with depth parameter (no country specified)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The geo_subdivisions route should return subdivisions at a specific depth
when depth parameter is provided without country:

    # Test depth=1 (level 1 subdivisions only)
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?depth=1")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> all(item["depth"] == 1 for item in response["items"])
    True

    # Test depth=2 (level 2 subdivisions only)
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?depth=2")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> all(item["depth"] == 2 for item in response["items"])
    True


Get subdivisions with depth parameter (country specified)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The geo_subdivisions route should return subdivisions at a specific depth
when depth parameter is provided with country:

    # Test depth=0 (returns all subdivisions - depth 1 + depth 2)
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES&depth=0")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> response["country"] == "ES"
    True
    >>> response["depth"] == 0
    True
    >>> "depth" in response["items"][0]
    True

    # Test depth=1 (level 1 subdivisions - states/provinces)
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES&depth=1")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> response["country"] == "ES"
    True
    >>> response["depth"] == 1
    True
    >>> all(item["depth"] == 1 for item in response["items"])
    True

    # Test depth=2 (level 2 subdivisions - counties/districts)
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES&depth=2")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> response["country"] == "ES"
    True
    >>> response["depth"] == 2
    True
    >>> all(item["depth"] == 2 for item in response["items"])
    True

    # Test negative depth (returns all subdivisions - depth 1 + depth 2)
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES&depth=-1")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> response["country"] == "ES"
    True
    >>> response["depth"] is None
    True
    >>> "depth" in response["items"][0]
    True


Get subdivisions for non-existent country
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The geo_subdivisions route should return an error for non-existent countries:

    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=XX")
    >>> response = json.loads(browser.contents)
    >>> response["count"] == 0
    True
    >>> "error" in response
    True
    >>> "Country not found" in response["error"]
    True


Get subdivisions for US with depth 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test getting subdivisions for US at depth 2 (states and counties):

    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=US&depth=2")
    >>> response = json.loads(browser.contents)
    >>> response["count"] >= 0
    True
    >>> response["country"] == "US"
    True
    >>> response["depth"] == 2
    True
    >>> all(item["depth"] == 2 for item in response["items"])
    True


Test parent_code logic
~~~~~~~~~~~~~~~~~~~~~

Test that parent_code is correctly set based on depth:

    # Level 1 subdivisions should have country_code as parent_code
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES&depth=1")
    >>> response = json.loads(browser.contents)
    >>> if response["count"] > 0:
    ...     level1_item = response["items"][0]
    ...     level1_item["parent_code"] == level1_item["country_code"]
    True

    # Level 2 subdivisions should have their actual parent_code
    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES&depth=2")
    >>> response = json.loads(browser.contents)
    >>> if response["count"] > 0:
    ...     level2_item = response["items"][0]
    ...     level2_item["parent_code"] != level2_item["country_code"]
    True


Unauthenticated user
~~~~~~~~~~~~~~~~~~~~

Log out:

    >>> logout()

The geo_subdivisions route should be accessible to unauthenticated users:

    >>> browser.open(api_base_url + "/geographic/subdivisions_schema?country=ES")
    >>> response = json.loads(browser.contents)
    >>> response["count"] > 0
    True 