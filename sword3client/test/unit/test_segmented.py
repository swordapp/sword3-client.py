from unittest import TestCase

from sword3client import SWORD3Client

from sword3common.exceptions import SeamlessException
from sword3common import constants
from sword3common.test.fixtures import SegmentedUploadFixtureFactory, StatusFixtureFactory

from sword3client.test.mocks.connection import MockHttpLayer

import json
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

    def test_04_segmented_file_upload_status(self):
        TEMP_URL = "http://example.com/temporary"

        doc = SegmentedUploadFixtureFactory.segmented_upload_status([1,2,3], [4,5])
        client = SWORD3Client(http=MockHttpLayer(200, json.dumps(doc), {"Content-Type" : "application/json"}))

        try:
            dr = client.segmented_upload_status(TEMP_URL)
        except SeamlessException as e:
            print(e.message)

    def test_05_create_object_with_temporary_file(self):
        SERVICE_URL = "http://example.com/service"
        TEMP_URL = "http://example.com/temporary"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))
        try:
            dr = client.create_object_with_temporary_file(SERVICE_URL, TEMP_URL, "test.zip", "application/octet-stream")
        except SeamlessException as e:
            print(e.message)

    def test_06_append_temporary_file(self):
        OBJ_URL = "http://example.com/object/1"
        TEMP_URL = "http://example.com/temporary"
        BODY = json.dumps(StatusFixtureFactory.status_document())

        client = SWORD3Client(http=MockHttpLayer(200, BODY, None))
        try:
            dr = client.append_temporary_file(OBJ_URL, TEMP_URL, "test.zip", "application/octet-stream")
        except SeamlessException as e:
            print(e.message)

    def test_07_replace_file_with_temporary_file(self):
        FILE_URL = "http://example.com/object/1/file/1"
        TEMP_URL = "http://example.com/temporary"

        client = SWORD3Client(http=MockHttpLayer(204, None, None))
        try:
            dr = client.replace_file_with_temporary_file(FILE_URL, TEMP_URL, "test.zip", "application/octet-stream")
        except SeamlessException as e:
            print(e.message)

    def test_08_replace_fileset_with_temporary_file(self):
        FILESET_URL = "http://example.com/object/1/files"
        TEMP_URL = "http://example.com/temporary"

        client = SWORD3Client(http=MockHttpLayer(204, None, None))
        try:
            dr = client.replace_fileset_with_temporary_file(FILESET_URL, TEMP_URL, "test.zip", "application/octet-stream")
        except SeamlessException as e:
            print(e.message)

    def test_09_replace_object_with_temporary_file(self):
        OBJ_URL = "http://example.com/object/1"
        TEMP_URL = "http://example.com/temporary"

        BODY = json.dumps(StatusFixtureFactory.status_document())
        client = SWORD3Client(http=MockHttpLayer(200, BODY, None))
        try:
            dr = client.replace_object_with_temporary_file(OBJ_URL, TEMP_URL, "test.zip", "application/octet-stream")
        except SeamlessException as e:
            print(e.message)