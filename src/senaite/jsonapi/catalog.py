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
# Copyright 2017-2023 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api as senaiteapi
from DateTime import DateTime
from Products.CMFPlone.CatalogTool import CatalogTool
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex
from senaite.jsonapi import api
from senaite.jsonapi import logger
from senaite.jsonapi import request as req
from senaite.jsonapi import underscore as _
from senaite.jsonapi.interfaces import ICatalog
from senaite.jsonapi.interfaces import ICatalogQuery
from zope import interface
from ZPublisher import HTTPRequest


SEARCHABLE_TEXT_INDEXES = [
    "listing_searchable_text",
    "SearchableText",
    "Title",
]


class Catalog(object):
    """Plone catalog adapter
    """
    interface.implements(ICatalog)

    def __init__(self, context):
        self._catalogs = {}

    def search(self, query):
        """search the catalog
        """
        logger.info("Catalog query={}".format(query))
        # Support to set the catalog as a request parameter
        catalogs = _.to_list(req.get("catalog", None))
        if catalogs:
            return senaiteapi.search(query, catalog=catalogs)
        # Delegate to the search API of Bika LIMS
        return senaiteapi.search(query)

    def __call__(self, query):
        return self.search(query)

    def get_catalog(self):
        name = req.get("catalog", "portal_catalog")
        if name not in self._catalogs:
            # Get the catalog directly from senaite api
            cat = senaiteapi.get_tool(name)
            if isinstance(cat, CatalogTool):
                self._catalogs[name] = cat
        return self._catalogs[name]

    def get_schema(self):
        catalog = self.get_catalog()
        return catalog.schema()

    def get_indexes(self):
        """get all indexes managed by this catalog

        TODO: Combine indexes of relevant catalogs depending on the portal_type
        which is searched for.
        """
        catalog = self.get_catalog()
        return catalog.indexes()

    def get_index(self, name):
        """get an index by name

        TODO: Combine indexes of relevant catalogs depending on the portal_type
        which is searched for.
        """
        catalog = self.get_catalog()
        index = catalog._catalog.getIndex(name)
        logger.debug("get_index={} of catalog '{}' --> {}".format(
            name, catalog.__name__, index))
        return index

    def get_searchable_text_indexes(self):
        """Returns a list of searchable text indexes
        """
        catalog = self.get_catalog()
        indexes = catalog._catalog.indexes
        searchable_text_indexes = []
        for k, v in indexes.items():
            if type(v) == ZCTextIndex:
                searchable_text_indexes.append(k)
        return searchable_text_indexes

    def to_index_value(self, value, index):
        """Convert the value for a given index
        """

        # ZPublisher records can be passed to the catalog as is.
        if isinstance(value, HTTPRequest.record):
            return value

        if isinstance(index, basestring):
            index = self.get_index(index)

        if index.id == "portal_type":
            return filter(lambda x: x, _.to_list(value))
        if index.meta_type == "DateIndex":
            return DateTime(value)
        if index.meta_type == "BooleanIndex":
            return bool(value)
        if index.meta_type == "KeywordIndex":
            return value.split(",")

        return value


class CatalogQuery(object):
    """Catalog query adapter
    """
    interface.implements(ICatalogQuery)

    def __init__(self, catalog):
        self.catalog = catalog

    def make_query(self, **kw):
        """create a query suitable for the catalog
        """
        query = kw.pop("query", {})

        query.update(self.get_request_query())
        query.update(self.get_custom_query())
        query.update(self.get_keyword_query(**kw))

        sort_on, sort_order = self.get_sort_spec()
        if sort_on and "sort_on" not in query:
            query.update({"sort_on": sort_on})
        if sort_order and "sort_order" not in query:
            query.update({"sort_order": sort_order})

        logger.info("make_query:: query={} | catalog={}".format(
            query, self.catalog))

        return query

    def get_request_query(self):
        """Checks the request for known catalog indexes and converts the values
        to fit the type of the catalog index.

        :param catalog: The catalog to build the query for
        :type catalog: ZCatalog
        :returns: Catalog query
        :rtype: dict
        """
        query = {}

        # only known indexes get observed
        indexes = self.catalog.get_indexes()

        for index in indexes:
            # Check if the request contains a parameter named like the index
            value = req.get(index)
            # No value found, continue
            if value is None:
                continue
            # Convert the found value to format understandable by the index
            index_value = self.catalog.to_index_value(value, index)
            # Conversion returned None, continue
            if index_value is None:
                continue
            # Append the found value to the query
            query[index] = index_value

        return query

    def get_custom_query(self):
        """Extracts custom query keys from the index.

        Parameters which get extracted from the request:

            `q`: Passes the value to an ZCTextIndex
            `path`: Creates a path query
            `recent_created`: Creates a date query
            `recent_modified`: Creates a date query

        :param catalog: The catalog to build the query for
        :type catalog: ZCatalog
        :returns: Catalog query
        :rtype: dict
        """
        query = {}

        # searchable text queries
        q = req.get_query()
        if q:
            # search index to use
            search_index = None
            # get all available ZCTextIndexes
            indexes = self.catalog.get_searchable_text_indexes()
            # prioritize search indexes
            for idx in SEARCHABLE_TEXT_INDEXES:
                if idx in indexes:
                    search_index = idx
                    break

            if search_index:
                # use the found search index
                query[search_index] = q
            elif len(indexes) > 0:
                # use any first found ZCTextIndex
                query[indexes[0]] = q
            else:
                logger.warn("No ZCTextIndex found in the catalog "
                            "to search for 'q=%s'" % q)

        # physical path queries
        path = req.get_path()
        if path:
            query["path"] = {'query': path, 'depth': req.get_depth()}

        # special handling for recent created/modified
        recent_created = req.get_recent_created()
        if recent_created:
            date = api.calculate_delta_date(recent_created)
            query["created"] = {'query': date, 'range': 'min'}

        recent_modified = req.get_recent_modified()
        if recent_modified:
            date = api.calculate_delta_date(recent_modified)
            query["modified"] = {'query': date, 'range': 'min'}

        return query

    def get_keyword_query(self, **kw):
        """Generates a query from the given keywords.
        Only known indexes make it into the generated query.

        :returns: Catalog query
        :rtype: dict
        """
        query = dict()

        # Only known indexes get observed
        indexes = self.catalog.get_indexes()

        # Handle additional keyword parameters
        for k, v in kw.iteritems():
            # handle uid in keywords
            if k.lower() == "uid":
                k = "UID"
            # handle portal_type in keywords
            if k.lower() == "portal_type":
                if v:
                    v = _.to_list(v)
            if k not in indexes:
                logger.warn("Skipping unknown keyword parameter '%s=%s'" % (k, v))
                continue
            if v is None:
                logger.warn("Skip None value in kw parameter '%s=%s'" % (k, v))
                continue
            logger.debug("Adding '%s=%s' to query" % (k, v))
            query[k] = v

        return query

    def get_sort_spec(self):
        """Build sort specification
        """
        all_indexes = self.catalog.get_indexes()
        si = req.get_sort_on(allowed_indexes=all_indexes)
        so = req.get_sort_order()
        return si, so
