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
# Copyright 2017-2026 by it's authors.
# Some rights reserved, see README and LICENSE.

import unittest

from senaite.jsonapi.webdav import allow_api_verbs
from senaite.jsonapi.webdav import is_api_request


class FakeRequest(object):
    def __init__(self, method="GET", path_info="/"):
        self._data = {"REQUEST_METHOD": method, "PATH_INFO": path_info}
        # Zope's default; the subscriber may flip it to 0.
        self.maybe_webdav_client = 1

    def get(self, key, default=None):
        return self._data.get(key, default)


class FakeEvent(object):
    def __init__(self, request):
        self.request = request


class TestIsApiRequest(unittest.TestCase):

    def test_matches_explicit_view_segment(self):
        self.assertTrue(is_api_request("/senaite/@@API/senaite/v1/uid"))

    def test_matches_acquisition_form_segment(self):
        self.assertTrue(is_api_request("/senaite/API/senaite/v1/uid"))

    def test_no_match_for_plain_content(self):
        self.assertFalse(is_api_request("/senaite/clients/client-1"))

    def test_no_substring_false_positive(self):
        # "APIfolder" is not the "API" segment.
        self.assertFalse(is_api_request("/senaite/APIfolder/doc"))


class TestAllowApiVerbs(unittest.TestCase):

    def _run(self, method, path):
        req = FakeRequest(method, path)
        allow_api_verbs(FakeEvent(req))
        return req

    def test_patch_to_api_clears_flag(self):
        req = self._run("PATCH", "/senaite/@@API/senaite/v1/uid")
        self.assertEqual(req.maybe_webdav_client, 0)

    def test_put_to_api_clears_flag(self):
        req = self._run("PUT", "/senaite/@@API/senaite/v1/uid")
        self.assertEqual(req.maybe_webdav_client, 0)

    def test_delete_to_api_clears_flag(self):
        req = self._run("DELETE", "/senaite/@@API/senaite/v1/uid")
        self.assertEqual(req.maybe_webdav_client, 0)

    def test_get_is_untouched(self):
        req = self._run("GET", "/senaite/@@API/senaite/v1/uid")
        self.assertEqual(req.maybe_webdav_client, 1)

    def test_post_is_untouched(self):
        req = self._run("POST", "/senaite/@@API/senaite/v1/uid")
        self.assertEqual(req.maybe_webdav_client, 1)

    def test_put_to_non_api_content_is_untouched(self):
        # A genuine WebDAV PUT to content must keep its flag so real
        # WebDAV keeps working.
        req = self._run("PUT", "/senaite/clients/client-1")
        self.assertEqual(req.maybe_webdav_client, 1)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestIsApiRequest))
    suite.addTest(makeSuite(TestAllowApiVerbs))
    return suite
