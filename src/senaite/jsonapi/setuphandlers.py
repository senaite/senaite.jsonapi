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

from Products.PlonePAS.setuphandlers import activatePluginInterfaces
from senaite.jsonapi import logger
from senaite.jsonapi import PRODUCT_NAME
from senaite.jsonapi.pas.plugin import JWTAuthenticationPlugin


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
