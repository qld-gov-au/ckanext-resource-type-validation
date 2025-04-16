# encoding: utf-8

'''Tests for the ckanext.qgov extension MIME type validation.
'''

import unittest

if __name__ == '__main__':
    from resource_type_validation import ResourceTypeValidator, \
        normalize_whitespace
else:
    from .resource_type_validation import ResourceTypeValidator, \
        normalize_whitespace

from ckan.logic import ValidationError
from werkzeug.datastructures import FileStorage as FlaskFileStorage


generic_text_type = 'text/plain'
text_type = 'text/csv'
generic_binary_type = 'application/octet-stream'
application_type = 'application/pdf'
archive_type = 'application/zip'

coalesce_types = [
    ([text_type], text_type),
    ([text_type, None], text_type),
    ([application_type, None], application_type),
    ([None, text_type], text_type),
    ([None, application_type], application_type),
    ([None, text_type, None, text_type, None], text_type),
    # Test that more specific candidates can override 'text/plain'
    # and 'application/octet-stream' if 'allow_override' is set.
    ([generic_text_type, text_type], text_type),
    ([None, generic_text_type], generic_text_type),
    ([None, text_type, generic_text_type], text_type),
    ([None, 'application/xml', generic_text_type], 'application/xml'),
    ([application_type, generic_binary_type], application_type),
    ([None, application_type, generic_binary_type], application_type),
    ([None, 'x-gis/x-shapefile', generic_binary_type], 'x-gis/x-shapefile'),
    ([None, archive_type], archive_type),
    (['text/xml', 'application/xml', generic_text_type], 'text/xml'),
    ([generic_text_type, 'application/xml', 'text/xml'], 'application/xml'),
]

sample_files = [
    ('ASampleDatabase.accdb', 'ACCDB',
     ['application/msaccess', 'application/x-msaccess']),
    ('example.asc', 'ASC', 'application/x-ascii-grid'),
    ('example.cdf', 'CDF', ['application/x-cdf', 'application/x-netcdf']),
    ('foo.csv', 'CSV', 'text/csv'),
    ('fortran-bug.csv', 'CSV', 'text/csv'),
    ('example.docx', 'DOCX', 'application/'
     'vnd.openxmlformats-officedocument.wordprocessingml.document'),
    ('example.docx', 'DOCX', ['application/msword', 'application/'
     'vnd.openxmlformats-officedocument.wordprocessingml.document']),
    ('sample.ecw', 'ECW', 'application/octet-stream'),
    ('example.kmz', 'KMZ', 'application/vnd.google-earth.kmz'),
    ('example.xml', 'XML', ['text/xml', 'application/xml']),
    ('dummy.pdf', 'PDF', 'application/pdf'),
    ('zoning.gdb', 'GDB', 'application/x-filegdb'),
    ('sample.geojson', 'GeoJSON', 'application/json'),
    ('ntf_nord.geotiff', 'GeoTIFF', 'image/tiff'),
    ('example.gpkg', 'GPKG', ['application/x-sqlite3', 'application/vnd.sqlite3']),
    ('example.gpx', 'GPX', 'application/xml'),
    ('example.html', 'HTML', 'text/html'),
    ('sample1.jp2', 'JP2', 'image/jp2'),
    ('sample_0.JPEG', 'JPEG', 'image/jpeg'),
    ('example.mtl', 'MTL', 'model/mtl'),
    ('example.n3', 'N3', 'text/n3'),
    ('dodecahedron.obj', 'OBJ', 'text/plain'),
    ('file-sample_100kB.rtf', 'RTF', ['application/rtf', 'text/rtf']),
    ('example.shp', 'SHP', 'x-gis/x-shapefile'),
    ('example.sparql', 'SPARQL', 'application/sparql-query'),
    ('Boundary.TAB', 'TAB', 'text/plain'),
    ('belgium.topojson', 'TOPOJSON', 'application/json'),
    ('Sample.tsv', 'TSV', 'text/tab-separated-values'),
    ('example.txt', 'TXT', 'text/plain'),
    ('example.wfs', 'WFS', 'application/xml'),
    ('example.wmts', 'WMTS', 'application/xml'),
    ('example.xlsx', 'XLSX', 'application/'
     'vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ('example.xlsx', 'XLSX', ['application/vnd.ms-excel', 'application/'
     'vnd.openxmlformats-officedocument.spreadsheetml.sheet']),
    ('example.doc', 'DOC', 'application/msword'),
    ('example.json', 'JSON', 'application/json'),
    ('example.kml', 'KML', 'application/vnd.google-earth.kml+xml'),
    ('Assets3_Data.mdb', 'MDB',
     ['application/msaccess', 'application/x-msaccess']),
    ('example.nc', 'NC', ['application/x-cdf', 'application/x-netcdf']),
    ('example.ppt', 'PPT', 'application/vnd.ms-powerpoint'),
    ('mixed-types-example.ppt', 'PPT', 'application/vnd.ms-powerpoint'),
    ('sample.pptx', 'PPTX', 'application/'
     'vnd.openxmlformats-officedocument.presentationml.presentation'),
    ('example.rdf', 'RDF', 'application/rdf+xml'),
    ('example.xls', 'XLS', 'application/vnd.ms-excel'),
    ('example.png', 'PNG', 'image/png'),
    ('example.tif', 'TIF', 'image/tiff'),
    # well-formed archives can specify any format
    ('example.zip', 'ZIP', 'application/zip'),
    ('example.zip', 'PDF', 'application/zip'),
    ('example.zip', 'DOC', 'application/zip'),
    ('example.parquet', 'PARQUET', 'application/octet-stream'),
    ('example.pqt', 'PARQUET', 'application/octet-stream'),
]

sample_file_rejections = [
    # file contents and format are PDF, but extension is CSV
    ('dummy.pdf', 'example.csv', 'PDF'),
    # file contents and extension are PDF, but format is XML
    ('dummy.pdf', 'example.pdf', 'XML'),
    # file extension and format are PDF, but contents are text
    ('eicar.com.pdf', 'example.pdf', 'PDF'),
    # file is an archive, but has a different extension
    ('example.zip', 'example.pdf', 'PDF'),
    # extension is ZIP, but file isn't really an archive
    ('eicar.com.pdf', 'example.zip', 'PDF'),
    ('eicar.com.pdf', 'example.zip', 'ZIP'),
]

sample_links = [
    'http://example.com/foo.csv',
    'http://ckan:5000/dataset/foo'
]


class TestMimeTypeValidation(unittest.TestCase):
    """ Test that potential MIME type candidates are correctly coalesced
    to a best fit.
    """

    def setUp(self):
        self.validator = ResourceTypeValidator({'ckan.site_url': 'http://ckan:5000/'})

    def test_equal_types(self):
        """ Test that equal types are treated as interchangeable.
        """
        self.assertTrue(self.validator.type_equals('application/xml',
                                                   'text/xml'))
        self.assertFalse(self.validator.type_equals('application/xml',
                                                    'text/plain'))
        self.assertEqual(self.validator.coalesce_mime_types(
            ['text/xml', 'application/xml']), 'text/xml')
        self.assertEqual(self.validator.coalesce_mime_types(
            ['application/xml', 'text/xml']), 'application/xml')

    def test_coalesce_candidates(self):
        """ Test that missing candidates are gracefully ignored.
        """
        for input_types, expected_type in coalesce_types:
            self.assertEqual(self.validator.coalesce_mime_types(input_types),
                             expected_type)

    def test_reject_override_not_configured(self):
        """ Test that more specific candidates cannot override
        'text/plain' and 'application/octet-stream' if 'allow_override'
        is set to False.
        """
        self.assertRaises(ValidationError,
                          self.validator.coalesce_mime_types,
                          [generic_text_type, text_type],
                          False)
        self.assertRaises(ValidationError,
                          self.validator.coalesce_mime_types,
                          [application_type, generic_binary_type],
                          False)

    def test_reject_override_incompatible_prefix(self):
        """ Test that candidates cannot override 'text/plain'
        with a different prefix.
        """
        self.assertRaises(ValidationError, self.validator.coalesce_mime_types,
                          [generic_text_type, application_type])

    # Full validation tests

    def test_recognise_file_types(self):
        """ Test that sample files are correctly sniffed.
        """
        for filename, specified_format, expected_type in sample_files:
            sample_file = open("test/resources/" + filename, "rb")
            upload = FlaskFileStorage(filename=filename,
                                      stream=sample_file)
            resource = {'url': filename,
                        'format': specified_format,
                        'upload': upload}

            try:
                self.validator.validate_resource_mimetype(resource)
                error_msg = '{} has an unexpected MIME type {}'.format(
                    filename, resource['mimetype'])
                if isinstance(expected_type, list):
                    assert_function = self.assertIn
                else:
                    assert_function = self.assertEqual
                # print(resource, expected_type, error_msg)
                assert_function(
                    resource['mimetype'], expected_type, error_msg)
            finally:
                sample_file.close()

    def test_reject_bad_file_types(self):
        """ Test that invalid filename/format/content combinations
        are rejected.
        """
        for filename, url, specified_format in sample_file_rejections:
            sample_file = open("test/resources/" + filename, "rb")
            upload = FlaskFileStorage(filename=url,
                                      stream=sample_file)
            resource = {'format': specified_format,
                        'upload': upload}
            try:
                self.assertRaises(ValidationError,
                                  self.validator.validate_resource_mimetype,
                                  resource)
                self.assertIsNone(resource.get('mimetype'))
            finally:
                sample_file.close()

    # Tests without file contents

    def test_revalidate_uploads_without_file(self):
        """ Test that resource of type 'upload' with no upload data
        have their URL and format compared, just no content sniffing.
        """
        resource = {'url': 'example.csv', 'format': 'PDF'}
        self.assertRaises(ValidationError,
                          self.validator.validate_resource_mimetype, resource)

        resource['format'] = 'CSV'
        self.validator.validate_resource_mimetype(resource)

    def test_no_validation_on_link_resources(self):
        """ Test that link-type resources do not have their file types
        validated, since they're not under our control.
        """
        for url in sample_links:
            resource = {'url': url, 'format': 'HTML'}
            self.validator.validate_resource_mimetype(resource)
            self.assertIsNone(resource.get('mimetype'))

    # Test error messages

    def test_error_contact(self):
        """ Test that the error messages are populated correctly.
        """
        self.assertEqual(
            normalize_whitespace(self.validator.invalid_upload_message),
            normalize_whitespace(
                '''This file type is not supported.
                If possible, upload the file in another format.
                If you continue to have problems, contact the site owner.'''))

        self.assertEqual(
            normalize_whitespace(self.validator.mismatching_upload_message),
            normalize_whitespace(
                '''Mismatched file type. Please ensure that the selected
                format is compatible with the file extension and file contents.
                Unable to determine whether the file is of type '{}' or '{}'.
                If possible, upload the file in another format.
                If you continue to have problems, contact the site owner.''')
        )

        self.validator = ResourceTypeValidator({
            'ckanext.resource_validation.support_contact':
                'the Ministry of Silly Walks.'
        })
        self.assertEqual(
            normalize_whitespace(self.validator.invalid_upload_message),
            normalize_whitespace(
                '''This file type is not supported.
                If possible, upload the file in another format.
                If you continue to have problems, contact the
                Ministry of Silly Walks.'''))

        self.assertEqual(
            normalize_whitespace(self.validator.mismatching_upload_message),
            normalize_whitespace(
                '''Mismatched file type. Please ensure that the selected
                format is compatible with the file extension and file contents.
                Unable to determine whether the file is of type '{}' or '{}'.
                If possible, upload the file in another format.
                If you continue to have problems, contact the
                Ministry of Silly Walks.''')
        )


if __name__ == '__main__':
    unittest.main()
