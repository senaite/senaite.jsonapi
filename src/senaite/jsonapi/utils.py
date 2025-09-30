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

import six


def to_utf8(value):
    if isinstance(value, six.text_type):
        return value.encode("utf-8")
    elif isinstance(value, list):
        return map(to_utf8, value)
    elif isinstance(value, dict):
        return {
            to_utf8(key): to_utf8(value)
            for key, value in six.iteritems(value)
        }
    return value
