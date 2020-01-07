import unittest
import json
import shutil
import os

from sword3client.client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.exceptions import SWORD3AuthenticationError, SWORD3NotFound, SWORD3WireError
from sword3client.lib import paths

from sword3common.test.fixtures.status import StatusFixtureFactory
from sword3common.test.fixtures.metadata import MetadataFixtureFactory
from sword3common.models.status import StatusDocument
from sword3common.models.metadata import Metadata

class TestObjectMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.tmpFiles = []

    def tearDown(self) -> None:
        for tmpFile in self.tmpFiles:
            path = paths.rel2abs(__file__, "..", "tmp", tmpFile)
            os.remove(path)

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

    def test_03_get_file(self):
        FILE_URL = "http://example.com/objects/10/files/1"

        filename = "test_object_methods.test_03_get_file.bin"
        data_in = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        data_out = paths.rel2abs(__file__, "..", "tmp", filename)
        self.tmpFiles.append(filename)

        with open(data_in, "rb") as f:
            client = SWORD3Client(http=MockHttpLayer(200, stream=f))
            with client.get_file(FILE_URL) as stream:
                with open(data_out, 'wb') as g:
                    shutil.copyfileobj(stream, g)

        d1 = paths.sha256(data_in)
        d2 = paths.sha256(data_out)

        assert d1.hexdigest() == d2.hexdigest()

