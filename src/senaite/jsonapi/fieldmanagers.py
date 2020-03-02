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

import dateutil
import mimetypes

from zope import interface
from zope.schema._bootstrapinterfaces import WrongType

from DateTime import DateTime
from AccessControl import Unauthorized
from Products.Archetypes.utils import mapply

from senaite.jsonapi import api
from senaite.jsonapi import logger
from senaite.jsonapi import underscore as u
from senaite.jsonapi.interfaces import IFieldManager


class ZopeSchemaFieldManager(object):
    """Adapter to get/set the value of Zope Schema Fields
    """
    interface.implements(IFieldManager)

    def __init__(self, field):
        self.field = field

    def get_field_name(self):
        return self.field.getName()

    def get(self, instance, **kw):
        """Get the value of the field
        """
        return self._get(instance, **kw)

    def set(self, instance, value, **kw):
        """Set the value of the field
        """
        return self._set(instance, value, **kw)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        return value or default

    def _set(self, instance, value, **kw):
        """Set the value of the field
        """
        logger.debug("DexterityFieldManager::set: value=%r" % value)

        # Check if the field is read only
        if self.field.readonly:
            raise Unauthorized("Field is read only")

        fieldname = self.get_field_name()
        # id fields take only strings
        if fieldname == "id":
            value = str(value)

        try:
            # Validate
            self.field.validate(value)

            # TODO: Check security on the field level
            return self.field.set(instance, value)
        except WrongType:
            logger.warn("WrongType: Field={} Value={}".format(self.field, value))
        except:  # noqa
            logger.warn("Unknown Exception: Field={} Value={}".format(self.field, value))

    def _get(self, instance, **kw):
        """Get the value of the field
        """
        logger.debug("DexterityFieldManager::get: instance={} field={}"
                     .format(instance, self.field))

        # TODO: Check security on the field level
        return self.field.get(instance)


class DatetimeFieldManager(ZopeSchemaFieldManager):
    """Adapter to get/set the value of Datetime Fields
    """
    interface.implements(IFieldManager)

    def set(self, instance, value, **kw):
        if value and isinstance(value, basestring):
            value = dateutil.parser.parse(value)
        self.field.validate(value)
        return self.field.set(instance, value)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        if not value:
            return ""
        if callable(value):
            value = value()
        return api.to_iso_date(value, default=default)


class RichTextFieldManager(ZopeSchemaFieldManager):
    """Adapter to get/set the value of Rich Text Fields
    """
    interface.implements(IFieldManager)

    def set(self, instance, value, **kw):
        from plone.app.textfield.value import RichTextValue
        value = RichTextValue(raw=value,
                              outputMimeType=self.field.output_mime_type)
        return self._set(instance, value, **kw)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        if value:
            return value.output
        return value


class NamedFileFieldManager(ZopeSchemaFieldManager):
    """Adapter to get/set the value of Named File Fields
    """
    interface.implements(IFieldManager)

    def get_size(self, instance):
        """Return the file size of the file
        """
        value = self.get(instance)
        return getattr(value, "size", 0)

    def get_data(self, instance):
        """Return the file data
        """
        value = self.get(instance)
        return getattr(value, "data", "")

    def get_filename(self, instance):
        """Get the filename
        """
        value = self.get(instance)
        return getattr(value, "filename", "")

    def get_content_type(self, instance):
        """Get the content type of the file object
        """
        value = self.get(instance)
        return getattr(value, "contentType", "")

    def get_download_url(self, instance, default=None):
        """Calculate the download url
        """
        download = default
        # calculate the download url
        download = "{url}/@@download/{fieldname}/{filename}".format(
            url=api.get_url(instance),
            fieldname=self.get_field_name(),
            filename=self.get_filename(instance),
        )
        return download

    def set(self, instance, value, **kw):
        logger.debug("NamedFileFieldManager::set:File field"
                     "detected ('%r'), base64 decoding value", self.field)

        data = str(value).decode("base64")
        filename = kw.get("filename") or kw.get("id") or kw.get("title")
        contentType = kw.get("mimetype") or kw.get("content_type")

        if contentType:
            # create NamedFile with content type information
            value = self.field._type(data=data,
                                     contentType=contentType,
                                     filename=filename)
        else:
            # create NamedFile w/o content type information
            # -> will be guessed by the extension of the filename
            value = self.field._type(data=data, filename=filename)

        return self.field.set(instance, value)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        return api.get_file_info(instance, self.get_field_name())


class NamedImageFieldManager(NamedFileFieldManager):
    """Adapter to get/set the value of Named Image Fields
    """
    interface.implements(IFieldManager)


class RelationListFieldManager(ZopeSchemaFieldManager):
    """Adapter to get/set the value of Z3C Relation Lists
    """
    interface.implements(IFieldManager)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)

        out = []
        for rel in value:
            if rel.isBroken():
                logger.warn("Skipping broken relation {}".format(repr(rel)))
                continue
            obj = rel.to_object
            out.append(api.get_url_info(obj))
        return out


class ATFieldManager(object):
    """Adapter to get/set the value of AT Fields
    """
    interface.implements(IFieldManager)

    def __init__(self, field):
        self.field = field
        self.name = self.get_field_name()

    def get_field(self):
        """Get the adapted field
        """
        return self.field

    def get_field_name(self):
        """Get the field name
        """
        return self.field.getName()

    def get(self, instance, **kw):
        """Get the value of the field
        """
        return self._get(instance, **kw)

    def set(self, instance, value, **kw):
        """Set the value of the field
        """
        return self._set(instance, value, **kw)

    def _set(self, instance, value, **kw):
        """Set the value of the field
        """
        logger.debug("ATFieldManager::set: value=%r" % value)

        # check field permission
        if not self.field.checkPermission("write", instance):
            raise Unauthorized("You are not allowed to write the field {}"
                               .format(self.name))

        # check if field is writable
        if not self.field.writeable(instance):
            raise Unauthorized("Field {} is read only."
                               .format(self.name))

        # id fields take only strings
        if self.name == "id":
            value = str(value)

        # get the field mutator
        mutator = self.field.getMutator(instance)

        # Inspect function and apply *args and **kwargs if possible.
        mapply(mutator, value, **kw)

        return True

    def _get(self, instance, **kw):
        """Get the value of the field
        """
        logger.debug("ATFieldManager::get: instance={} field={}"
                     .format(instance, self.field))

        # check the field permission
        if not self.field.checkPermission("read", instance):
            raise Unauthorized("You are not allowed to read the field {}"
                               .format(self.name))

        # return the field value
        return self.field.get(instance)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        return value or default


class ComputedFieldManager(ATFieldManager):
    """Adapter to get/set the value of Text Fields
    """
    interface.implements(IFieldManager)

    def set(self, instance, value, **kw):
        """Not applicable for Computed Fields
        """
        logger.warn("Setting is not allowed for computed fields")

    def get(self, instance, **kw):
        """Get the value of the field
        """
        # Gracefully avoid programming errors in Computed fields
        try:
            return self._get(instance, **kw)
        except AttributeError:
            logger.error("Could not get the value of the computed field '{}'"
                         .format(self.get_field_name()))
            return None


class TextFieldManager(ATFieldManager):
    """Adapter to get/set the value of Text Fields
    """
    interface.implements(IFieldManager)


class DateTimeFieldManager(ATFieldManager):
    """Adapter to get/set the value of DateTime Fields
    """
    interface.implements(IFieldManager)

    def set(self, instance, value, **kw):
        """Converts the value into a DateTime object before setting.
        """
        if value:
            try:
                value = DateTime(value)
            except SyntaxError:
                logger.warn("Value '{}' is not a valid DateTime string"
                            .format(value))
                return False

        self._set(instance, value, **kw)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        return api.to_iso_date(value) or default


class FileFieldManager(ATFieldManager):
    """Adapter to get/set the value of File Fields
    """
    interface.implements(IFieldManager)

    def get_size(self, instance):
        """Return the file size of the file
        """
        return self.field.get_size(instance)

    def get_data(self, instance):
        """Return the file data
        """
        value = self.get(instance)
        return getattr(value, "data", "")

    def get_filename(self, instance):
        """Get the filename
        """
        filename = self.field.getFilename(instance)
        if filename:
            return filename

        fieldname = self.get_field_name()
        content_type = self.get_content_type(instance)
        extension = mimetypes.guess_extension(content_type)

        return fieldname + extension

    def get_content_type(self, instance):
        """Get the content type of the file object
        """
        return self.field.getContentType(instance)

    def get_download_url(self, instance, default=None):
        """Calculate the download url
        """
        download = default
        # calculate the download url
        download = "{url}/at_download/{fieldname}".format(
            url=instance.absolute_url(), fieldname=self.get_field_name())
        return download

    def set(self, instance, value, **kw):
        """Decodes base64 value and set the file object
        """
        value = str(value).decode("base64")

        # handle the filename
        if "filename" not in kw:
            logger.debug("FielFieldManager::set: No Filename detected "
                         "-> using title or id")
            kw["filename"] = kw.get("id") or kw.get("title")

        self._set(instance, value, **kw)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        return api.get_file_info(instance, self.get_field_name())


class ReferenceFieldManager(ATFieldManager):
    """Adapter to get/set the value of Reference Fields
    """
    interface.implements(IFieldManager)

    def __init__(self, field):
        super(ReferenceFieldManager, self).__init__(field)
        self.allowed_types = field.allowed_types
        self.multi_valued = field.multiValued

    def is_multi_valued(self):
        return self.multi_valued

    def set(self, instance, value, **kw):  # noqa
        """Set the value of the refernce field
        """
        ref = []

        # The value is an UID
        if api.is_uid(value):
            ref.append(api.get_object_by_uid(value))

        # The value is already an object
        if api.is_at_content(value):
            ref.append(value)

        # The value is a dictionary
        # -> handle it like a catalog query
        if u.is_dict(value):
            results = api.search(portal_type=self.allowed_types, **value)
            ref = map(api.get_object, results)

        # The value is a list
        if u.is_list(value):
            for item in value:
                # uid
                if api.is_uid(item):
                    ref.append(api.get_object_by_uid(item))
                    continue

                # object
                if api.is_at_content(item):
                    ref.append(api.get_object(item))
                    continue

                # path
                if api.is_path(item):
                    ref.append(api.get_object_by_path(item))
                    continue

                # dict (catalog query)
                if u.is_dict(item):
                    # If there is UID of objects, just use it.
                    uid = item.get('uid', None)
                    if uid:
                        obj = api.get_object_by_uid(uid)
                        ref.append(obj)
                    else:
                        results = api.search(portal_type=self.allowed_types, **item)
                        objs = map(api.get_object, results)
                        ref.extend(objs)
                    continue

                # Plain string
                # -> do a catalog query for title
                if isinstance(item, basestring):
                    results = api.search(portal_type=self.allowed_types, title=item)
                    objs = map(api.get_object, results)
                    ref.extend(objs)
                    continue

        # The value is a physical path
        if api.is_path(value):
            ref.append(api.get_object_by_path(value))

        # Handle non multi valued fields
        if not self.multi_valued:
            if len(ref) > 1:
                raise ValueError("Multiple values given for single valued "
                                 "field {}".format(repr(self.field)))
            else:
                ref = ref[0]
        return self._set(instance, ref, **kw)

    def json_data(self, instance, default=None):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        if value and self.is_multi_valued():
            return map(api.get_url_info, value)
        elif value and not self.is_multi_valued():
            return api.get_url_info(value)
        return value or default


class ProxyFieldManager(ATFieldManager):
    """Adapter to get/set the value of Proxy Fields
    """
    interface.implements(IFieldManager)

    def __init__(self, field):
        super(ProxyFieldManager, self).__init__(field)
        self.proxy_object = None
        self.proxy_field = None

    def get_proxy_object(self, instance):
        """Get the proxy object of the field
        """
        return self.field.get_proxy(instance)

    def get_proxy_field(self, instance):
        """Get the proxied field of this field
        """
        proxy_object = self.get_proxy_object(instance)
        if not proxy_object:
            return None
        return proxy_object.getField(self.name)

    def set(self, instance, value, **kw):
        """Set the value of the (proxy) field
        """
        proxy_field = self.get_proxy_field(instance)
        if proxy_field is None:
            return None
        # set the field with the proper field manager of the proxy field
        fieldmanager = IFieldManager(proxy_field)
        return fieldmanager.set(instance, value, **kw)


class ARAnalysesFieldManager(ATFieldManager):
    """Adapter to get/set the value of Bika AR Analyses Fields
    """
    interface.implements(IFieldManager)

    def json_data(self, instance, default=[]):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        out = map(api.get_url_info, value)
        return out or default

    def set(self, instance, value, **kw):
        """
        Set Analyses to an AR

        :param instance: Analysis Request
        :param value: Single AS UID or a list of dictionaries containing AS UIDs
        :param kw: Additional keyword parameters passed to the field
        """

        if not isinstance(value, (list, tuple)):
            value = [value]

        uids = []
        for item in value:
            uid = None
            if isinstance(item, dict):
                uid = item.get("uid")
            if api.is_uid(value):
                uid = item
            if uid is None:
                logger.warn("Could extract UID of value")
                continue
            uids.append(uid)

        analyses = map(api.get_object_by_uid, uids)
        self._set(instance, analyses, **kw)


class UIDReferenceFieldManager(ATFieldManager):
    """Adapter to get/set the value of UIDReferenceFields
    """
    interface.implements(IFieldManager)

    def __init__(self, field):
        super(UIDReferenceFieldManager, self).__init__(field)
        self.multi_valued = field.multiValued

    def json_data(self, instance, default={}):
        """Get a JSON compatible value
        """
        value = self.get(instance)
        if not value:
            return default
        if self.multi_valued:
            out = map(api.get_url_info, value)
        else:
            out = value
        return out or default

    def set(self, instance, value, **kw):  # noqa
        """Set the value of the uid reference field
        """
        ref = []
        # The value is an UID
        if api.is_uid(value):
            ref.append(value)

        # The value is a dictionary, get the UIDs.
        if u.is_dict(value):
            ref = ref.append(value.get("uid"))

        # The value is already an object
        if api.is_at_content(value):
            ref.append(value)

        # The value is a list
        if u.is_list(value):
            for item in value:
                # uid
                if api.is_uid(item):
                    ref.append(item)
                # dict (catalog query)
                elif u.is_dict(item):
                    # If there is UID of objects, just use it.
                    uid = item.get('uid', None)
                    if uid:
                        ref.append(uid)

        # Handle non multi valued fields
        if not self.multi_valued:
            if len(ref) > 1:
                raise ValueError("Multiple values given for single valued "
                                 "field {}".format(repr(self.field)))
            else:
                ref = ref[0]

        return self._set(instance, ref, **kw)
