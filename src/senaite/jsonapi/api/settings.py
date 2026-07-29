# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.JSONAPI.
#
# SENAITE.JSONAPI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
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

"""Registry and control-panel settings helpers.

Both routes (`/registry`, `/settings`) delegate here. Kept apart from
the general api namespace so the control-panel schema wiring lives in
one place.
"""

from bika.lims import api as bika_api
from plone import api as ploneapi
from plone.i18n.interfaces import ILanguageSchema
from Products.CMFPlone.interfaces.controlpanel import IDateAndTimeSchema
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from Products.CMFPlone.interfaces.controlpanel import IMaintenanceSchema
from Products.CMFPlone.interfaces.controlpanel import ISecuritySchema
from Products.CMFPlone.interfaces.controlpanel import IUserGroupsSettingsSchema  # noqa: E501
from senaite.core.api import dtime
from zope.component import getAdapter
from zope.schema import getFieldNames


CONTROLPANEL_INTERFACE_MAPPING = {
    "mail": [IMailSchema],
    "language": [ILanguageSchema],
    "dateandtime": [IDateAndTimeSchema],
    "usergroups": [IUserGroupsSettingsSchema, ISecuritySchema],
    "maintenance": [IMaintenanceSchema],
}


def to_json_value(value):
    """Coerce a registry value into a JSON serializable form.

    Registry records may hold dates or datetimes (and containers of them),
    which the JSON encoder used by the route cannot serialize.

    :param value: The raw registry value
    :returns: A JSON serializable value
    """
    if isinstance(value, (list, tuple)):
        return [to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: to_json_value(val) for key, val in value.items()}
    # datetime and Zope DateTime
    if dtime.is_dt(value) or dtime.is_DT(value):
        return dtime.to_iso_format(value)
    # pure date, which to_iso_format does not handle
    if dtime.is_d(value):
        return value.isoformat()
    return value


def get_registry_records_by_keyword(keyword=None):
    """Return registry records whose name contains `keyword`.

    If `keyword` is None, returns every record.
    """
    portal_reg = ploneapi.portal.get_tool(name="portal_registry")
    records = {}
    for record in portal_reg.records:
        if keyword is None or keyword.lower() in record.lower():
            value = bika_api.get_registry_record(record)
            records[record] = to_json_value(value)
    return records


def get_settings_by_keyword(keyword=None):
    """Return control-panel settings grouped by keyword.

    If `keyword` is None, returns every mapped section. Raises KeyError
    for an unknown keyword (route layer maps it to 404).
    """
    # Lazy: url_for lives in api/__init__.py which imports this module.
    from senaite.jsonapi.api import url_for

    def pack(key):
        merged = {}
        for iface in CONTROLPANEL_INTERFACE_MAPPING[key]:
            merged.update(get_settings_from_interface(iface))
        return {
            key: merged,
            "api_url": url_for("senaite.jsonapi.v1.settings", key=key),
        }

    if keyword is None:
        return [pack(k) for k in CONTROLPANEL_INTERFACE_MAPPING]
    return [pack(keyword)]


def get_settings_from_interface(iface):
    """Return the JSON-serializable settings from a control-panel schema
    interface as {schema_name: {field: value, ...}}.
    """
    # Lazy: is_json_serializable lives in api/__init__.py which imports
    # this module.
    from senaite.jsonapi.api import is_json_serializable

    schema = getAdapter(bika_api.get_portal(), iface)
    values = {}
    for field_name in getFieldNames(iface):
        value = getattr(schema, field_name, None)
        if is_json_serializable(value):
            values[field_name] = value
    return {iface.getName(): values}
