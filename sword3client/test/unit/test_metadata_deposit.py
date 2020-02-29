from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer

from sword3common import Metadata, ServiceDocument, exceptions
from sword3common.test.fixtures import StatusFixtureFactory, MetadataFixtureFactory
from sword3common import exceptions

import json


class TestService(TestCase):
    def test_01_create_object_with_metadata(self):

        SD_URL = "http://example.com/service-document"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        sd = ServiceDocument()
        sd.service_url = SD_URL

        try:
            dr = client.create_object_with_metadata(sd, metadata)
        except exceptions.SeamlessException as e:
            print(e.message)

    def test_02_append_metadata(self):
        OBJ_URL = "http://example.com/obect/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(200, BODY, HEADERS))

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test Append")
        metadata.add_dcterms_field("rights", "Some of them")
        metadata.add_field("custom", "value")

        try:
            dr = client.append_metadata(OBJ_URL, metadata)
        except exceptions.SeamlessException as e:
            print(e.message)

    def test_03_replace_metadata(self):
        MD_URL = "http://example.com/obect/10/metadata"

        client = SWORD3Client(http=MockHttpLayer(204))

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test Append")
        metadata.add_dcterms_field("rights", "Some of them")
        metadata.add_field("custom", "value")

        try:
            dr = client.replace_metadata(MD_URL, metadata)
        except exceptions.SeamlessException as e:
            print(e.message)

    def test_04_delete_metadata(self):
        MD_URL = "http://example.com/obect/10/metadata"
        client = SWORD3Client(http=MockHttpLayer(204))
        dr = client.delete_metadata(MD_URL)

    def test_05_get_metadata(self):
        MD_URL = "http://example.com/objects/10/metadata"

        client = SWORD3Client(
            http=MockHttpLayer(200, json.dumps(MetadataFixtureFactory.metadata()))
        )
        obj = client.get_metadata(MD_URL)
        assert isinstance(obj, Metadata)

        client = SWORD3Client(http=MockHttpLayer(401))
        with self.assertRaises(exceptions.NoCredentialsSupplied):
            try:
                obj = client.get_metadata(MD_URL)
            except exceptions.NoCredentialsSupplied as e:
                assert e.request_url == MD_URL
                assert e.response is not None
                assert e.message is not None
                raise

        client = SWORD3Client(http=MockHttpLayer(403))
        with self.assertRaises(exceptions.AuthenticationFailed):
            obj = client.get_metadata(MD_URL)

        client = SWORD3Client(http=MockHttpLayer(404))
        with self.assertRaises(exceptions.NotFound):
            obj = client.get_metadata(MD_URL)

        client = SWORD3Client(http=MockHttpLayer(405))
        with self.assertRaises(exceptions.MethodNotAllowed):
            obj = client.get_metadata(MD_URL)

    def test_06_replace_object_with_metadata(self):
        OBJ_URL = "http://example.com/object/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())

        client = SWORD3Client(http=MockHttpLayer(200, BODY))

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        try:
            dr = client.replace_object_with_metadata(OBJ_URL, metadata)
        except exceptions.SeamlessException as e:
            print(e.message)
