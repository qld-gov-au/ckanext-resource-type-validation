[![Tests](https://github.com/qld-gov-au/ckanext-resource-type-validation/actions/workflows/test.yml/badge.svg)](https://github.com/qld-gov-au/ckanext-resource-type-validation/actions/workflows/test.yml)
=============
ckanext-resource-type-validation
=============

Overview
--------
A CKAN extension that performs stricter validation of resource formats
for uploaded files, ensuring that the file extension, file contents,
and selected resource format are all compatible with each other.

1. Reduces workload on back of house staff in fixing up format selection
on miscategorised files.
1. Better restrictions on allowed formats by also running them through
magic/type sniffing systems. This ensures that an invalid file can't be
uploaded by selecting a random format and changing the file type ending.

It is also possible to specify whitelists of allowed file extensions
and/or allowed MIME types. Future development may allow a blacklist, but
this is harder to make reliable.

This affects only uploaded resources. URL resources are not validated.

See [the configuration file](https://github.com/qld-gov-au/ckanext-resource-type-validation/blob/main/ckanext/resource_type_validation/resources/resource_types.json)
for more details.

Installation
------------

To install ``ckanext-resource-type-validation``:

1. Install CKAN 2.9+.

1. Activate your CKAN virtual environment, eg:

    ```
    . /usr/lib/ckan/default/bin/activate
    ```

1. Install the extension into your virtual environment:

    ```
    git clone https://github.com/qld-gov-au/ckanext-resource-type-validation.git
    cd ckanext-resource-type-validation
    pip install -e .
    pip install -r requirements.txt
    ```

1. Add ``resource_type_validation`` to the ``ckan.plugins`` setting in
your CKAN config file (by default the config file is located at
``/etc/ckan/default/production.ini``).

1. Restart CKAN. Eg if you've deployed CKAN with Apache on Ubuntu:

    sudo service apache2 reload


# Configuration

    ckan.plugins = resource_type_validation

## Optional

    # Path to the configuration file for specifying file types and their
    # relationships. Defaults to built-in
    # ckanext/resource_type_validation/resources/resource_types.json
    ckanext.resource_validation.types_file = /path/to/file.json

    # Support contact to list in any error messages
    ckanext.resource_validation.support_contact = webmaster@example.com

    # Whitelist of allowed mimetypes
    ckan.mimetypes_allowed = application/pdf,text/plain,text/xml

The configuration file can contain the following, all optional and in
any order:

* ``allowed_extensions``: A list of allowed file extensions, case-insensitive.
If this is not specified, any extension is allowed.

* ``allowed_overrides``: A dictionary specifying which MIME types are
treated as subtypes of others, eg ``application/xml`` is a subtype of
``text/plain``, and anything is a subtype of ``application/octet-stream``.
So, a file named ``example.xml`` with content that looks like ``text/plain``,
and a specified resource format of "XML", would be accepted.
The format of each entry is `"parent-type": ["sub-type1", "sub-type2"]`.
Wildcards are partially supported; an override can be a single asterisk
to allow any other type to be a subtype (typically used for
``application/octet-stream``), or it can have the form ``prefix/*`` to
allow any type with that prefix to be a subtype (eg ``text/*`` can
override ``text/plain``).

* ``equal_types``: A list of lists of types that are interchangeable,
eg ``text/xml`` is the same as ``application/xml``.
This can be used in a similar manner to ``allowed_overrides``, but is
bidirectional, and will affect the resulting displayed format.
Overrides will attempt to use the most specific subtype,
whereas equal types take whichever is encountered first.
For example, a file named ``example.rdf`` and containing XML data,
with ``application/rdf+xml`` as an override for ``application/xml``,
would have a resource mimetype of ``application/rdf+xml``, but if
``application/xml`` and ``application/rdf+xml`` are configured as equal
types, then the resource mimetype might be simply ``application/xml``.

* ``archive_types``: A list of types that are archives and require
special handling, eg ``application/zip``. Archives can specify any
resource format (since the format might refer to the archive contents),
so long as the archive is well-formed (file extension and contents match).

* ``generic_types``: A list of types that are 'generic' ie supertype to
many others (eg ``text/plain`` and ``application/octet-stream``).
File contents of these types can be overridden with a subtype,
but if the file extension or format matches them, then that cannot be
overridden. Eg a file with ``text/plain`` content could specify a CSV
extension and format, but a file with ``.txt`` extension could not
specify a "CSV" format. Similarly, a resource with "TXT" format
could not have a ``.xml`` extension.
This is intended to prevent browser-based content-sniffing attacks,
where a file with an innocuous extension like ``.txt`` may be handled
in a different way by the browser based on the apparent type of its
contents.

* ``extra_mimetypes``: A dictionary of additional mappings to add to the
Python ``mimetypes`` library for guessing types based on file extensions.
The format of each entry is `".extension": "mime-type"`.
For example, a site that expects to upload Quartus Tabular Text Files
might define the ``.ttf`` extension to have ``text/plain`` MIME type:

  ```
  "extra_mimetypes": {
    ".ttf": "text/plain"
  }
  ```

Testing
-------

To run the tests:

1. Activate your CKAN virtual environment, eg `. /usr/lib/ckan/default/bin/activate`

1. Switch to the extension directory, eg `cd /usr/lib/ckan/default/src/ckanext-resource-type-validation`

1. Install test requirements: `pip install -r dev-requirements.txt`

1. Run the tests. This can be done in multiple ways.

    1. Execute the test class directly:

        ```
        python ckanext/resource_type_validation/test_mime_type_validation.py
        ```

    1. Run ``pytest``


Alternative testing with Docker
-------

The Docker-based test environment currently relies on *nix shell scripts.

1. Install [Docker Compose](https://docs.docker.com/compose/) and [Ahoy](https://github.com/ahoy-cli/ahoy).

1. Build the test containers: `CKAN_VERSION=<version eg 2.11> bin/build.sh`

1. Run unit tests: `ahoy test-unit`

1. Set up test data: `ahoy install-site`

1. Run scenario tests: `ahoy test-bdd`

