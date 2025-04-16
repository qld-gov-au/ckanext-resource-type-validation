# encoding: utf-8

from typing import Any

from ckan import plugins

from .resource_type_validation import ResourceTypeValidator


class ResourceTypeValidationPlugin(plugins.SingletonPlugin):
    """Apply stricter validation to uploaded resource formats.
    Filename, file contents, and specified format must resolve to
    compatible types.
    """
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    validator: 'ResourceTypeValidator|None' = None

    # IConfigurable

    def configure(self, config: plugins.toolkit.CKANConfig):
        self.validator = ResourceTypeValidator(config)

    # IResourceController

    # CKAN 2.9
    def before_create(self, context: Any, data_dict: 'dict[str, Any]'):
        self.before_resource_create(context, data_dict)

    def before_update(self, context: Any, current: 'dict[str, Any]', data_dict: 'dict[str, Any]'):
        self.before_resource_update(context, current, data_dict)

    # CKAN 2.10
    def before_resource_create(self, context: Any, data_dict: 'dict[str, Any]'):
        """ Check that uploads have an acceptable mime type.
        """
        assert self.validator
        self.validator.validate_resource_mimetype(data_dict)

    def before_resource_update(self, context: Any, current: 'dict[str, Any]', data_dict: 'dict[str, Any]'):
        """ Check that uploads have an acceptable mime type.
        """
        assert self.validator
        self.validator.validate_resource_mimetype(data_dict)
