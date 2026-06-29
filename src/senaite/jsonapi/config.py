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
# Copyright 2017-2025 by it's authors.
# Some rights reserved, see README and LICENSE.

from senaite.jsonapi import PRODUCT_NAME

# Default JWT lifetime (60 minutes, in seconds)
JWT_TOKENS_TIMEOUT = 60 * 60

# Name of the HttpOnly cookie used to carry the JWT token
JWT_COOKIE_ID = "token"

# Fallback header used to carry the JWT token when neither the
# Authorization Bearer header nor the cookie is set
JWT_HEADER_ID = "X-JWT-Auth-Token"

# Annotation key used to store the per-user JWT signing secrets on the
# portal (IAnnotations(portal)[KEY_STORAGE] is an OOBTree keyed by userid)
KEY_STORAGE = "%s.pas.keystorage" % PRODUCT_NAME
