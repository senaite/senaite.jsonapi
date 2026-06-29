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
# Copyright 2017-2025 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api
from Products.CMFPlone.interfaces import INonInstallable
from Products.PlonePAS.setuphandlers import activatePluginInterfaces
from senaite.jsonapi import logger
from senaite.jsonapi import PRODUCT_NAME
from senaite.jsonapi.config import KEY_STORAGE
from senaite.jsonapi.pas.plugin import ID as JWT_PLUGIN_ID
from senaite.jsonapi.pas.plugin import JWTAuthenticationPlugin
from zope.annotation.interfaces import IAnnotations
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    """Hide the uninstall profile from the Add-ons control panel so it
    is not listed as an installable add-on. The Add-ons panel only
    shows the `default` profile; the `uninstall` profile is applied
    automatically when the user clicks "Uninstall".
    """

    def getNonInstallableProfiles(self):  # noqa camelCase
        return [
            "%s:uninstall" % PRODUCT_NAME,
        ]

    def getNonInstallableProducts(self):  # noqa camelCase
        return []


def setup_handler(context):
    """Generic setup handler for senaite.jsonapi
    """
    install_file = "%s.txt" % PRODUCT_NAME
    if context.readDataFile(install_file) is None:
        return

    logger.info("%s setup handler [BEGIN]" % PRODUCT_NAME.upper())
    portal = context.getSite()

    setup_pas_plugin(portal)

    logger.info("%s setup handler [DONE]" % PRODUCT_NAME.upper())


def setup_pas_plugin(portal):
    """Register the JWT PAS plugin in the site's acl_users so JWT-based
    authentication becomes active.
    """
    plugin = JWTAuthenticationPlugin()
    plugin_id = plugin.getId()

    logger.info("Setup %s plugin ..." % plugin_id)

    pas = portal.acl_users
    if plugin_id not in pas.objectIds():
        # Add the plugin
        pas._setObject(plugin_id, plugin)  # noqa

        # Activate all supported interfaces for this plugin
        activatePluginInterfaces(pas, plugin_id)

        # Make our plugin the first one for these interfaces, so the JWT
        # token takes precedence over other extractors/authenticators
        ifaces = ["IExtractionPlugin", "IAuthenticationPlugin"]
        plugin_registry = pas.plugins
        for iface_name in ifaces:
            iface = plugin_registry._getInterfaceFromName(iface_name)  # noqa
            plugin_registry.movePluginsTop(iface, [plugin_id])

    logger.info("Setup %s plugin [DONE]" % plugin_id)


def uninstall_handler(context):
    """Generic setup uninstall handler for senaite.jsonapi
    """
    uninstall_file = "%s-uninstall.txt" % PRODUCT_NAME
    if context.readDataFile(uninstall_file) is None:
        return

    logger.info("%s uninstall handler [BEGIN]" % PRODUCT_NAME.upper())
    portal = context.getSite()

    remove_pas_plugin(portal)
    remove_keystorage(portal)

    logger.info("%s uninstall handler [DONE]" % PRODUCT_NAME.upper())


def remove_pas_plugin(portal):
    """Remove the JWT PAS plugin from the site's acl_users.
    """
    pas = portal.acl_users
    if JWT_PLUGIN_ID in pas.objectIds():
        logger.info("Remove %s plugin ..." % JWT_PLUGIN_ID)
        pas.manage_delObjects([JWT_PLUGIN_ID])


def remove_keystorage(portal):
    """Drop the per-user JWT signing secrets from the portal's
    annotations. All previously-issued tokens become unverifiable.
    """
    annotation = IAnnotations(api.get_portal())
    if KEY_STORAGE in annotation:
        logger.info("Remove %s key storage ..." % PRODUCT_NAME)
        del annotation[KEY_STORAGE]
