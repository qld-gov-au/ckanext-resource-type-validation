from setuptools import setup, find_packages

version = '1.0.5'

setup(
    name='ckanext-resource-type-validation',
    version=version,
    description='Apply stricter validation to CKAN resource formats',
    long_description="""Ensure that uploaded resources have matching filenames,\
formats, and file contents""",
    classifiers=[],
    keywords='',
    author='Queensland Online',
    author_email='qol.development@smartservice.qld.gov.au',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points="""
    [ckan.plugins]
    resource_type_validation=\
ckanext.resource_type_validation.plugin:ResourceTypeValidationPlugin
    """,
)
