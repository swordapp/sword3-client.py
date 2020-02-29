import unittest
import json
import os

from sword3client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.lib import paths

from sword3common.test.fixtures import StatusFixtureFactory
from sword3common import exceptions, StatusDocument


class TestObjectMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpFiles = []

    def tearDown(self) -> None:
        for tmpFile in self.tmpFiles:
            path = paths.rel2abs(__file__, "..", "tmp", tmpFile)
            os.remove(path)

    def test_01_get_object(self):
        OBJ_URL = "http://example.com/objects/10"

        client = SWORD3Client(
            http=MockHttpLayer(200, json.dumps(StatusFixtureFactory.status_document()))
        )
        obj = client.get_object(OBJ_URL)
        assert isinstance(obj, StatusDocument)

        client = SWORD3Client(http=MockHttpLayer(401))
        with self.assertRaises(exceptions.NoCredentialsSupplied):
            try:
                obj = client.get_object(OBJ_URL)
            except exceptions.NoCredentialsSupplied as e:
                assert e.request_url == OBJ_URL
                assert e.response is not None
                assert e.message is not None
                raise

        client = SWORD3Client(http=MockHttpLayer(403))
        with self.assertRaises(exceptions.AuthenticationFailed):
            obj = client.get_object(OBJ_URL)

        client = SWORD3Client(http=MockHttpLayer(404))
        with self.assertRaises(exceptions.NotFound):
            obj = client.get_object(OBJ_URL)

        client = SWORD3Client(http=MockHttpLayer(405))
        with self.assertRaises(exceptions.UnexpectedSwordException):
            obj = client.get_service(OBJ_URL)

    def test_02_delete_object(self):
        OBJ_URL = "http://example.com/objects/10"
        client = SWORD3Client(http=MockHttpLayer(204))
        dr = client.delete_object(OBJ_URL)
