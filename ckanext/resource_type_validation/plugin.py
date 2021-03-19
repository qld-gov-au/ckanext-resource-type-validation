# encoding: utf-8

from ckan import plugins

import resource_type_validation


class ResourceTypeValidationPlugin(plugins.SingletonPlugin):
    """Apply stricter validation to uploaded resource formats.
    Filename, file contents, and specified format must resolve to
    compatible types.
    """
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    # IConfigurer

    def update_config(self, config):
        """ Add our templates directory so we can add a config field.
        """
        plugins.toolkit.add_template_directory(config, 'templates')

    def update_config_schema(self, schema):
        """ Add a field to the schema to specify the support contact
        (usually an email address).
        """
        schema.update({
            'ckanext.resource_validation.support_contact': [
                plugins.toolkit.get_validator('ignore_missing')
            ]
        })

    # IResourceController

    def before_create(self, context, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        resource_type_validation.validate_resource_mimetype(data_dict)

    def before_update(self, context, existing_resource, data_dict):
        """ Check that uploads have an acceptable mime type.
        """
        resource_type_validation.validate_resource_mimetype(data_dict)
