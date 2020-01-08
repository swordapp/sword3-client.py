import unittest
import shutil
import os

from sword3client.client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.lib import paths

from sword3common import constants


class TestFile(unittest.TestCase):

    def setUp(self) -> None:
        self.tmpFiles = []

    def tearDown(self) -> None:
        for tmpFile in self.tmpFiles:
            path = paths.rel2abs(__file__, "..", "tmp", tmpFile)
            if os.path.exists(path):
                os.remove(path)

    def test_01_get_file(self):
        FILE_URL = "http://example.com/objects/10/files/1"

        filename = "test_file.test_01_get_file.bin"
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

    def test_02_replace_file(self):
        FILE_URL = "http://example.com/objects/10/files/1"

        filename = "test_file.test_02_get_file.bin"
        data_in = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")

        d1 = paths.sha256(data_in)

        client = SWORD3Client(http=MockHttpLayer(204))
        dr = client.replace_file(FILE_URL, data_in, "application/octet-stream", {constants.DIGEST_SHA_256 : d1.digest()})

    def test_03_delete_file(self):
        FILE_URL = "http://example.com/objects/10/files/1"
        client = SWORD3Client(http=MockHttpLayer(204))
        dr = client.delete_file(FILE_URL)
