# encoding: utf-8

from ckan import plugins

import resource_type_validation


class ResourceTypeValidationPlugin(plugins.SingletonPlugin):
    """Apply stricter validation to uploaded resource formats.
    Filename, file contents, and specified format must resolve to
    compatible types.
    """
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController

    def before_create(self, context, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        resource_type_validation.validate_resource_mimetype(data_dict)

    def before_update(self, context, existing_resource, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        resource_type_validation.validate_resource_mimetype(data_dict)
