from unittest import TestCase

from sword3client.client import SWORD3Client
from sword3common import constants

from io import BytesIO
import hashlib
import base64

class TestInvenio(TestCase):

    def test_01_create_object_with_binary(self):
        SD_URL = "http://localhost:8000/api/deposit"
        client = SWORD3Client()

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = "{x}={y}".format(x=constants.DIGEST_SHA_256, y=base64.b64encode(d.digest()))
        stream = BytesIO(bytes)

        dr = client.create_object_with_binary(SD_URL, stream, "test.bin", digest)
        print(dr.location)
