import unittest
import json

from sword3client.client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.exceptions import SWORD3AuthenticationError, SWORD3NotFound, SWORD3WireError

from sword3common.test.fixtures.status import StatusFixtureFactory
from sword3common.test.fixtures.metadata import MetadataFixtureFactory
from sword3common.models.status import StatusDocument
from sword3common.models.metadata import Metadata

class TestObjectMethods(unittest.TestCase):
    def test_01_get_object(self):
        OBJ_URL = "http://example.com/objects/10"

        client = SWORD3Client(http=MockHttpLayer(200, json.dumps(StatusFixtureFactory.status_document())))
        obj = client.get_object(OBJ_URL)
        assert isinstance(obj, StatusDocument)

        client = SWORD3Client(http=MockHttpLayer(401))
        with self.assertRaises(SWORD3AuthenticationError):
            try:
                obj = client.get_object(OBJ_URL)
            except SWORD3AuthenticationError as e:
                assert e.request_url == OBJ_URL
                assert e.response is not None
                assert e.message is not None
                raise

        client = SWORD3Client(http=MockHttpLayer(403))
        with self.assertRaises(SWORD3AuthenticationError):
            obj = client.get_object(OBJ_URL)

        client = SWORD3Client(http=MockHttpLayer(404))
        with self.assertRaises(SWORD3NotFound):
            obj = client.get_object(OBJ_URL)

        client = SWORD3Client(http=MockHttpLayer(405))
        with self.assertRaises(SWORD3WireError):
            obj = client.get_service(OBJ_URL)

    def test_02_get_metadata(self):
        MD_URL = "http://example.com/objects/10/metadata"

        client = SWORD3Client(http=MockHttpLayer(200, json.dumps(MetadataFixtureFactory.metadata())))
        obj = client.get_metadata(MD_URL)
        assert isinstance(obj, Metadata)

        client = SWORD3Client(http=MockHttpLayer(401))
        with self.assertRaises(SWORD3AuthenticationError):
            try:
                obj = client.get_metadata(MD_URL)
            except SWORD3AuthenticationError as e:
                assert e.request_url == MD_URL
                assert e.response is not None
                assert e.message is not None
                raise

        client = SWORD3Client(http=MockHttpLayer(403))
        with self.assertRaises(SWORD3AuthenticationError):
            obj = client.get_metadata(MD_URL)

        client = SWORD3Client(http=MockHttpLayer(404))
        with self.assertRaises(SWORD3NotFound):
            obj = client.get_metadata(MD_URL)

        client = SWORD3Client(http=MockHttpLayer(405))
        with self.assertRaises(SWORD3WireError):
            obj = client.get_metadata(MD_URL)

