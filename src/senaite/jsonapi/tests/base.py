# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.JSONAPI.
#
# SENAITE.JSONAPI is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2017-2020 by it's authors.
# Some rights reserved, see README and LICENSE.

import unittest2 as unittest
from bika.lims.testing import BASE_TESTING
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.testing import z2
from plone.testing.z2 import Browser


class SimpleTestLayer(PloneSandboxLayer):
    """Setup Plone with installed AddOn only
    """
    defaultBases = (BASE_TESTING, PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        super(SimpleTestLayer, self).setUpZope(app, configurationContext)

        # Load ZCML
        import bika.lims
        import senaite.jsonapi

        self.loadZCML(package=bika.lims)
        self.loadZCML(package=senaite.jsonapi)

        # Install product and call its initialize() function
        z2.installProduct(app, "senaite.jsonapi")

    def setUpPloneSite(self, portal):
        super(SimpleTestLayer, self).setUpPloneSite(portal)

        # Apply Setup Profile (portal_quickinstaller)
        # applyProfile(portal, "senaite.jsonapi:default")

        login(portal.aq_parent, SITE_OWNER_NAME)

        # Add some test users
        ROLES = ["LabManager", "LabClerk", "Analyst"]
        for role in ROLES:

            for user_nr in range(2):
                username = "test_%s_%s" % (role.lower(), user_nr)
                try:
                    member = portal.portal_registration.addMember(
                        username,
                        username,
                        properties={
                            "username": username,
                            "email": username + "@example.com",
                            "fullname": username})
                    # Add user to all specified groups
                    group_id = role + "s"
                    group = portal.portal_groups.getGroupById(group_id)
                    if group:
                        group.addMember(username)
                    # Add user to all specified roles
                    member._addRole(role)
                except ValueError:
                    pass  # user exists

        logout()

    def tearDownZope(self, app):
        # Uninstall product
        z2.uninstallProduct(app, "senaite.jsonapi")


###
# Use for simple tests (w/o contents)
###
SIMPLE_FIXTURE = SimpleTestLayer()
SIMPLE_TESTING = FunctionalTesting(
    bases=(SIMPLE_FIXTURE, ),
    name="senaite.jsonapi:SimpleTesting"
)


class SimpleTestCase(unittest.TestCase):
    layer = SIMPLE_TESTING

    def setUp(self):
        super(SimpleTestCase, self).setUp()

        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.request["ACTUAL_URL"] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["LabManager", "Manager"])

    def getBrowser(self,
                   username=TEST_USER_NAME,
                   password=TEST_USER_PASSWORD,
                   loggedIn=True):

        # Instantiate and return a testbrowser for convenience
        browser = Browser(self.portal)
        browser.addHeader('Accept-Language', 'en-US')
        browser.handleErrors = False
        if loggedIn:
            browser.open(self.portal.absolute_url())
            browser.getControl('Login Name').value = username
            browser.getControl('Password').value = password
            browser.getControl('Log in').click()
            self.assertTrue('You are now logged in' in browser.contents)
        return browser
