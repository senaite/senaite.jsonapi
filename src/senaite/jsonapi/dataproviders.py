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

from zope import interface
from zope import component

from plone.dexterity.interfaces import IDexterityContent

from AccessControl import Unauthorized
from Products.CMFCore.interfaces import ISiteRoot
from Products.ZCatalog.interfaces import ICatalogBrain
from Products.ATContentTypes.interfaces import IATContentType

from senaite.jsonapi import api
from senaite.jsonapi import logger
from senaite.jsonapi.interfaces import IInfo
from senaite.jsonapi.interfaces import ICatalog
from senaite.jsonapi.interfaces import IDataManager

_marker = object


class Base(object):
    """ Base Adapter
    """
    interface.implements(IInfo)

    def __init__(self, context):
        self.context = context
        self.keys = []
        self.ignore = []

        # Mapped attributes to extract from the object besides the schema keys.
        # These keys are always included
        self.attributes = {
            "id": "getId",
            "uid": "UID",
            "title": "Title",
            "description": "Description",
            "created": "created",
            "modified": "modified",
            "effective": "effective",
            "portal_type": "portal_type",
            "tags": "Subject",
            "author": "Creator",
            "path": "_x_get_physical_path",
            "parent_path": "_x_get_parent_path",
        }

    def _x_get_physical_path(self):
        """Generate the physical path
        """
        path = self.context.getPhysicalPath()
        return "/".join(path)

    def _x_get_parent_path(self):
        """Generate the parent path
        """
        path = self.context.getPhysicalPath()
        return "/".join(path[:-1])

    def to_dict(self):
        """ extract the data of the content and return it as a dictionary
        """

        # 1. extract the schema fields
        data = self.extract_fields()

        # 2. include custom key-value pairs listed in the mapping dictionary
        for key, attr in self.attributes.iteritems():
            if key in self.ignore:
                continue  # skip ignores
            # fetch the mapped attribute
            value = getattr(self.context, attr, None)
            if value is None:
                value = getattr(self, attr, None)
            # handle function calls
            if callable(value):
                value = value()
            # map the value to the given key from the mapping
            data[key] = api.to_json_value(self.context, key, value)
        return data

    def extract_fields(self):
        """Extract the given fieldnames from the object

        :returns: Schema name/value mapping
        :rtype: dict
        """

        # get the proper data manager for the object
        dm = IDataManager(self.context)

        # filter out ignored fields
        fieldnames = filter(lambda name: name not in self.ignore, self.keys)

        # schema mapping
        out = dict()

        for fieldname in fieldnames:
            try:
                # get the field value with the data manager
                fieldvalue = dm.json_data(fieldname)
            # https://github.com/collective/plone.jsonapi.routes/issues/52
            # -> skip restricted fields
            except Unauthorized:
                logger.debug("Skipping restricted field '%s'" % fieldname)
                continue
            except ValueError:
                logger.debug("Skipping invalid field '%s'" % fieldname)
                continue

            out[fieldname] = api.to_json_value(self.context, fieldname, fieldvalue)

        return out

    def __call__(self):
        return self.to_dict()


class ZCDataProvider(Base):
    """ Catalog Brain Adapter
    """
    interface.implements(IInfo)
    component.adapts(ICatalogBrain)

    def __init__(self, context):
        super(ZCDataProvider, self).__init__(context)
        catalog_adapter = ICatalog(context)
        # extract the metadata
        self.keys = catalog_adapter.get_schema()

        # ignore some metadata values, which we already mapped
        self.ignore = [
            'CreationDate',
            'Creator',
            'Date',
            'Description',
            'EffectiveDate',
            'ExpirationDate',
            'ModificationDate',
            'Subject',
            'Title',
            'Type',
            'UID',
            'cmf_uid',
            'getIcon',
            'getId',
            'getObjSize',
            'getRemoteUrl',
            'listCreators',
            'meta_type',
        ]

    def _x_get_parent_path(self):
        """Generate the parent path
        """
        path = self._x_get_physical_path().split("/")
        return "/".join(path[:-1])

    def _x_get_physical_path(self):
        """Generate the physical path
        """
        path = self.context.getPath()
        portal_path = api.get_path(api.get_portal())
        if portal_path not in path:
            return "{}/{}".format(portal_path, path)
        return path


class DexterityDataProvider(Base):
    """ Data Provider for Dexterity based content types
    """
    interface.implements(IInfo)
    component.adapts(IDexterityContent)

    def __init__(self, context):
        super(DexterityDataProvider, self).__init__(context)

        # get the behavior and schema fields from the data manager
        schema = api.get_schema(context)
        behaviors = api.get_behaviors(context)
        self.keys = schema.names() + behaviors.keys()


class ATDataProvider(Base):
    """ Archetypes Adapter
    """
    interface.implements(IInfo)
    component.adapts(IATContentType)

    def __init__(self, context):
        super(ATDataProvider, self).__init__(context)

        # get the schema fields from the data manager
        schema = api.get_schema(context)
        self.keys = schema.keys()


class SiteRootDataProvider(Base):
    """ Site Root Adapter
    """
    interface.implements(IInfo)
    component.adapts(ISiteRoot)

    def __init__(self, context):
        super(SiteRootDataProvider, self).__init__(context)
        # virtual keys, which are handled by the data manager
        self.keys = ["uid", "path"]
