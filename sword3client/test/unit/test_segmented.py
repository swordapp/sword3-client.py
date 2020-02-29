from unittest import TestCase

from sword3client import SWORD3Client

from sword3common.exceptions import SeamlessException
from sword3common import constants

from sword3client.test.mocks.connection import MockHttpLayer

import hashlib
import base64
import math
from io import BytesIO

class TestSegmented(TestCase):
    def test_01_initialise_segmented_upload(self):

        STAGING_URL = "http://example.com/staging"
        HEADERS = {"Location": "http://example.com/temporary"}

        client = SWORD3Client(http=MockHttpLayer(201, None, HEADERS))

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}

        segment_size = 10
        assembled_size = len(bytes)
        segment_count = math.ceil(assembled_size / segment_size)

        try:
            dr = client.initialise_segmented_upload(STAGING_URL, assembled_size, segment_count, segment_size, digest)
        except SeamlessException as e:
            print(e.message)

    def test_02_upload_file_segment(self):
        TEMP_URL = "http://example.com/temporary"

        client = SWORD3Client(http=MockHttpLayer(204, None, None))

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        stream = BytesIO(bytes)
        content_length = len(bytes)

        try:
            dr = client.upload_file_segment(TEMP_URL, stream, 3, digest, content_length)
        except SeamlessException as e:
            print(e.message)

    def test_03_abort_segmented_upload(self):
        TEMP_URL = "http://example.com/temporary"

        client = SWORD3Client(http=MockHttpLayer(204, None, None))

        try:
            dr = client.abort_segmented_upload(TEMP_URL)
        except SeamlessException as e:
            print(e.message)