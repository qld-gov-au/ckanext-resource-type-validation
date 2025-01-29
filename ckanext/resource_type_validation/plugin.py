# encoding: utf-8

import logging

from ckan import plugins

from .resource_type_validation import ResourceTypeValidator

LOG = logging.getLogger(__name__)


class ResourceTypeValidationPlugin(plugins.SingletonPlugin):
    """Apply stricter validation to uploaded resource formats.
    Filename, file contents, and specified format must resolve to
    compatible types.
    """
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    def configure(self, config):
        self.validator = ResourceTypeValidator()
        self.validator.configure(config)

    # IResourceController

    # CKAN 2.9
    def before_create(self, context, data_dict):
        self.before_resource_create(context, data_dict)

    def before_update(self, context, current, data_dict):
        self.before_resource_update(context, current, data_dict)

    # CKAN 2.10
    def before_resource_create(self, context, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        LOG.debug("Validating provided types for new resource")
        self.validator.validate_resource_mimetype(data_dict)

    def before_resource_update(self, context, current, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        LOG.debug("Validating provided types for updated resource")
        self.validator.validate_resource_mimetype(data_dict)
