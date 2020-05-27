VERSION
-------

Running this test from the buildout directory:

    bin/test test_doctests -t version


Test Setup
~~~~~~~~~~

Needed Imports:

    >>> import transaction
    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_PASSWORD

Functional Helpers:

    >>> def login(user=TEST_USER_ID, password=TEST_USER_PASSWORD):
    ...     browser.open(portal_url + "/login_form")
    ...     browser.getControl(name='__ac_name').value = user
    ...     browser.getControl(name='__ac_password').value = password
    ...     browser.getControl(name='submit').click()
    ...     assert("__ac_password" not in browser.contents)

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

Authenticated user
~~~~~~~~~~~~~~~~~~

Authenticate:

    >>> login()

The version route should be visible to authenticated users:

    >>> browser.open(api_base_url + "/version")
    >>> browser.contents
    '{"url": "http://nohost/plone/@@API/senaite/v1/version", "date": "...", "version": ..., "_runtime": ...}'

Unauthenticated user
~~~~~~~~~~~~~~~~~~~~

Log out:

    >>> logout()

The version route should be visible to unauthenticated users too:

    >>> browser.open(api_base_url + "/version")
    >>> browser.contents
    '{"url": "http://nohost/plone/@@API/senaite/v1/version", "date": "...", "version": ..., "_runtime": ...}'
