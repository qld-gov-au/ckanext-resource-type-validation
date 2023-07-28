# encoding: utf-8

from ckan import plugins

from .resource_type_validation import ResourceTypeValidator


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
        return self.before_resource_create(context, data_dict)

    def before_update(self, context, existing_resource, data_dict):
        return self.before_resource_update(context, existing_resource, data_dict)

    # CKAN 2.10
    def before_resource_create(self, context, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        self.validator.validate_resource_mimetype(data_dict)

    def before_resource_update(self, context, existing_resource, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        self.validator.validate_resource_mimetype(data_dict)
