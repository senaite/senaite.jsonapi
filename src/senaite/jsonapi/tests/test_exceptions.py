# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.JSONAPI.
#
# SENAITE.JSONAPI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2017-2026 by it's authors.
# Some rights reserved, see README and LICENSE.

"""The status a typed error carries, and when it is applied."""

import unittest

from senaite.jsonapi import exceptions


class FakeResponse(object):
    def __init__(self):
        self.status = None

    def setStatus(self, status):
        self.status = status


class FakeRequest(object):
    def __init__(self):
        self.response = FakeResponse()


class APIErrorStatusTestCase(unittest.TestCase):
    """An error carries its status; it does not apply it.

    The status reaches the response when plone.jsonapi.core renders the
    error envelope, which is the moment the error becomes the answer.
    Applied in the constructor instead, an error that was caught, and
    never answered with, left its status on whatever the request went
    on to return: a route that catches a ForbiddenError and then
    succeeds answered its complete result under a 403.
    """

    def setUp(self):
        self.request = FakeRequest()
        self._get_request = exceptions.req.getRequest
        exceptions.req.getRequest = lambda: self.request

    def tearDown(self):
        exceptions.req.getRequest = self._get_request

    def test_each_error_carries_its_own_status(self):
        self.assertEqual(exceptions.BadRequestError("x").status, 400)
        self.assertEqual(exceptions.UnauthorizedError("x").status, 401)
        self.assertEqual(exceptions.ForbiddenError("x").status, 403)
        self.assertEqual(exceptions.NotFoundError("x").status, 404)
        self.assertEqual(exceptions.APIError("x").status, 500)

    def test_an_explicit_status_wins(self):
        self.assertEqual(exceptions.APIError("x", status=418).status, 418)

    def test_constructing_one_leaves_the_response_alone(self):
        exceptions.ForbiddenError("not for you")
        self.assertIsNone(self.request.response.status)

    def test_the_message_is_what_str_gives(self):
        self.assertEqual(str(exceptions.NotFoundError("gone")), "gone")

    # The legacy alias is the one way to apply a status by hand, kept
    # for callers outside this package that still do.
    def test_set_status_applies_and_records_it(self):
        error = exceptions.APIError("x")
        error.setStatus(409)
        self.assertEqual(error.status, 409)
        self.assertEqual(self.request.response.status, 409)

    def test_set_status_outside_a_request_is_harmless(self):
        exceptions.req.getRequest = lambda: None
        exceptions.APIError("x").setStatus(409)

    def test_every_typed_error_is_an_api_error(self):
        for name in ("BadRequestError", "UnauthorizedError",
                     "ForbiddenError", "NotFoundError"):
            self.assertTrue(
                issubclass(getattr(exceptions, name), exceptions.APIError))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(APIErrorStatusTestCase))
    return suite
