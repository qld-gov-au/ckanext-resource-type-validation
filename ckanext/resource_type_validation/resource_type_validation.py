# encoding: utf-8
""" Verify that uploaded resources have consistent types;
file extension, file contents, and resource format should match.
"""

import json
from logging import getLogger
import magic
import mimetypes
import os
import re
import six

from ckan.lib.uploader import ALLOWED_UPLOAD_TYPES
from ckan.logic import ValidationError
from werkzeug.datastructures import FileStorage as FlaskFileStorage

LOG = getLogger(__name__)

IS_REMOTE_URL_PATTERN = re.compile(r'^[a-z+]+://')


def _get_underlying_file(wrapper):
    if isinstance(wrapper, FlaskFileStorage):
        return wrapper.stream
    return wrapper.file


def normalize_whitespace(text):
    return ' '.join(text.split())


class ResourceTypeValidator:

    def configure(self, config):
        types_file_name = config.get(
            'ckanext.resource_validation.types_file',
            os.path.join(os.path.dirname(__file__),
                         'resources',
                         'resource_types.json')
        )
        types_file = open(types_file_name)
        try:
            file_mime_config = json.load(types_file)
        finally:
            types_file.close()

        # Add allowed upload types that don't seem to be standard.
        # NB It's more important to match a sniffable type than an RFC type.
        for extension, mime_type in six.iteritems(
                file_mime_config.get('extra_mimetypes', {})
        ):
            mimetypes.add_type(mime_type, extension)

        allowed_extensions = file_mime_config.get('allowed_extensions', [])
        if allowed_extensions:
            LOG.debug("Allowed file extensions: %s", allowed_extensions)
            self.allowed_extensions_pattern = re.compile(
                r'.*\.(' + '|'.join(allowed_extensions) + ')$', re.I
            )

        self.allowed_overrides = file_mime_config.get('allowed_overrides', {})
        self.equal_types = file_mime_config.get('equal_types', [])
        self.archive_mimetypes = file_mime_config.get('archive_types', [])
        self.generic_mimetypes = file_mime_config.get(
            'generic_types', self.allowed_overrides.keys())
        error_contact = config.get(
            'ckanext.resource_validation.support_contact',
            'the site owner.'
        )

        self.invalid_upload_message = normalize_whitespace(
            '''This file type is not supported.
            If possible, upload the file in another format.
            If you continue to have problems, contact ''' + error_contact)
        self.mismatching_upload_message = normalize_whitespace(
            '''Mismatched file type. Please ensure that the selected format is
            compatible with the file extension and file contents.
            Unable to determine whether the file is of type '{}' or '{}'.
            If possible, upload the file in another format.
            If you continue to have problems, contact ''' + error_contact)

        self.allowed_mime_types = config.get(
            'ckan.mimetypes_allowed', '*').split(',')

    def validate_resource_mimetype(self, resource):
        upload_field_storage = resource.get('upload', None)
        if isinstance(upload_field_storage, ALLOWED_UPLOAD_TYPES) \
                and upload_field_storage.filename:
            filename = upload_field_storage.filename

            mime = magic.Magic(mime=True)
            upload_file = _get_underlying_file(upload_field_storage)
            # needs to be at least 2048 bytes to recognise DOCX properly
            sniffed_mimetype = mime.from_buffer(upload_file.read(2048))
            # go back to the beginning of the file buffer
            upload_file.seek(0, os.SEEK_SET)
            # When on old libmagic/file lookup, it needs the full file for type sniffing to be successful.
            if (sniffed_mimetype.startswith('Composite Document File V2 Document, corrupt')):
                sniffed_mimetype = mime.from_buffer(upload_file.read())
                # go back to the beginning of the file buffer
                upload_file.seek(0, os.SEEK_SET)

            LOG.debug('Upload sniffing indicates MIME type %s',
                      sniffed_mimetype)
            # print('Upload sniffing indicates MIME type ',
            #           sniffed_mimetype, upload_file, '\r\n')
        elif IS_REMOTE_URL_PATTERN.search(
                resource.get('url', 'http://example.com')
        ):
            LOG.debug('%s is not an uploaded resource, skipping validation',
                      resource.get('id', 'New resource'))
            return
        else:
            LOG.debug('No upload in progress for %s; just sanity-check',
                      resource.get('id', 'new resource'))
            filename = resource.get('url')
            sniffed_mimetype = None

        if (self.allowed_extensions_pattern
                and not self.allowed_extensions_pattern.search(filename)):
            raise ValidationError(
                {'upload': [self.invalid_upload_message]}
            )

        claimed_mimetype = resource.get('mimetype')
        LOG.debug("Upload claims to have MIME type %s", claimed_mimetype)

        filename_mimetype = mimetypes.guess_type(
            filename,
            strict=False)[0]
        LOG.debug("Upload filename indicates MIME type %s", filename_mimetype)

        format_mimetype = mimetypes.guess_type(
            'example.' + resource.get('format', ''),
            strict=False)[0]
        LOG.debug("Upload format indicates MIME type %s", format_mimetype)

        # Archives can declare any format, but only if they're well formed
        if any(type in self.archive_mimetypes
               for type in (filename_mimetype, sniffed_mimetype)):
            if self.type_equals(filename_mimetype, sniffed_mimetype)\
                    or self.is_valid_override(
                        filename_mimetype,
                        sniffed_mimetype)[0]:
                # well-formed archives can specify any format they want
                sniffed_mimetype = filename_mimetype = claimed_mimetype =\
                    format_mimetype or claimed_mimetype or filename_mimetype
            else:
                raise ValidationError(
                    {'upload': [
                        self.mismatching_upload_message.format(
                            filename_mimetype,
                            sniffed_mimetype)
                    ]}
                )

        # If the file extension or format matches a generic type,
        # then sniffing should say the same.
        # This is to prevent attacks based on browser sniffing.
        allow_override = filename_mimetype not in self.generic_mimetypes\
            and format_mimetype not in self.generic_mimetypes\
            or filename_mimetype in self.archive_mimetypes

        try:
            best_guess_mimetype = resource['mimetype'] = self.coalesce_mime_types(
                [filename_mimetype, format_mimetype, sniffed_mimetype,
                 claimed_mimetype],
                allow_override=allow_override
            )
        except ValidationError as e:
            LOG.debug("Best guess at MIME type failed %s - upload type: %s format type: %s sniffed: %s claimed: %s",
                      resource.get('url'), filename_mimetype, format_mimetype, sniffed_mimetype, claimed_mimetype)
            # print(resource.get('url'), ' upload type: ', filename_mimetype,' format type: ', format_mimetype,
            # "sniffed: ", sniffed_mimetype, " claimed: ", claimed_mimetype, 'failed', '\r\n')
            raise e

        LOG.debug("Best guess at MIME type is %s", best_guess_mimetype)
        if not self.is_mimetype_allowed(best_guess_mimetype):
            raise ValidationError(
                {'upload': [self.invalid_upload_message]}
            )

    def coalesce_mime_types(self, mime_types, allow_override=True):
        """ Compares a list of potential mime types and identifies
        the best candidate, ignoring any that are None.

        Throws ckan.logic.ValidationError if any candidates conflict.
        Returns 'application/octet-stream' if all candidates are None.

        'allow_override' controls the treatment of 'application/octet-stream'
        and 'text/plain' candidates. If True, then more specific types will
        be able to override these types (within limits, eg 'text/csv' and
        'application/xml' can override 'text/plain', but 'application/pdf'
        cannot). If False, then all types must exactly match, or
        ValidationError will be thrown.
        """
        best_candidate = None
        for mime_type in mime_types:
            if not mime_type or self.type_equals(mime_type, best_candidate):
                continue
            if not best_candidate:
                best_candidate = mime_type
                continue
            if allow_override:
                is_valid, subtype = self.is_valid_override(
                    best_candidate, mime_type)
                if is_valid:
                    best_candidate = subtype
                    continue
            raise ValidationError(
                {'upload': [
                    self.mismatching_upload_message.format(
                        best_candidate, mime_type)
                ]}
            )

        return best_candidate or 'application/octet-stream'

    def type_equals(self, type1, type2):
        """ Checks whether type1 and type2 are to be considered the same
        eg 'text/xml' and 'application/xml' are interchangeable.
        """
        if type1 == type2:
            return True
        for type_list in self.equal_types:
            if type1 in type_list and type2 in type_list:
                return True
        else:
            return False

    def is_valid_override(self, mime_type1, mime_type2):
        """ Returns True if one of the two types can be considered a subtype
        of the other, eg 'text/csv' can override 'text/plain'.

        If True, then the second return value is the more specific type,
        otherwise it is None.
        """
        def matches_override_list(mime_type, override_list):
            for override_type in override_list:
                if override_type == '*'\
                        or self.type_equals(override_type, mime_type):
                    return True
                override_parts = override_type.split('/', 1)
                if len(override_parts) == 2 and override_parts[1] == '*'\
                        and override_parts[0] == mime_type.split('/')[0]:
                    return True
            else:
                return False

        for generic_type, override_list in six.iteritems(
                self.allowed_overrides
        ):
            if self.type_equals(generic_type, mime_type1)\
                    and matches_override_list(mime_type2, override_list):
                return True, mime_type2
            if self.type_equals(generic_type, mime_type2)\
                    and matches_override_list(mime_type1, override_list):
                return True, mime_type1
        else:
            return False, None

    def is_mimetype_allowed(self, mime_type):
        for allowed_mime_type in self.allowed_mime_types:
            if allowed_mime_type == '*'\
                    or self.type_equals(allowed_mime_type, mime_type):
                return True
        return False
