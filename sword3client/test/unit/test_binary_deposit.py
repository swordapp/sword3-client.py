from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.lib import paths

from sword3common.test.fixtures import StatusFixtureFactory
from sword3common.exceptions import SeamlessException
from sword3common import constants

from sword3client.test.mocks.connection import MockHttpLayer

import json
from io import BytesIO
import hashlib
import base64


class TestBinaryDeposit(TestCase):
    def test_01_create_object_with_binary(self):

        SD_URL = "http://example.com/service-document"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        stream = BytesIO(bytes)

        try:
            dr = client.create_object_with_binary(SD_URL, stream, "test.bin", digest)
        except SeamlessException as e:
            print(e.message)

    def test_02_create_object_with_package(self):

        SD_URL = "http://example.com/service-document"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))

        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        with open(bag, "rb") as stream:
            try:
                dr = client.create_object_with_package(
                    SD_URL,
                    stream,
                    "test.zip",
                    digest,
                    content_type="application/zip",
                    packaging=constants.PACKAGE_SWORDBAGIT,
                )
            except SeamlessException as e:
                print(e.message)

    def test_03_add_binary(self):
        OBJ_URL = "http://example.com/object/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": OBJ_URL}

        client = SWORD3Client(http=MockHttpLayer(200, BODY, HEADERS))

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        stream = BytesIO(bytes)

        try:
            dr = client.add_binary(OBJ_URL, stream, "test.bin", digest)
        except SeamlessException as e:
            print(e.message)

    def test_04_add_package(self):
        OBJ_URL = "http://example.com/object/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": OBJ_URL}

        client = SWORD3Client(http=MockHttpLayer(200, BODY, HEADERS))

        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        with open(bag, "rb") as stream:
            try:
                dr = client.add_package(
                    OBJ_URL,
                    stream,
                    "test.zip",
                    digest,
                    content_type="application/zip",
                    packaging=constants.PACKAGE_SWORDBAGIT,
                )
            except SeamlessException as e:
                print(e.message)

    def test_05_replace_object_with_binary(self):
        OBJ_URL = "http://example.com/object/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())

        client = SWORD3Client(http=MockHttpLayer(200, BODY))

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        stream = BytesIO(bytes)

        try:
            dr = client.replace_object_with_binary(OBJ_URL, stream, "test.bin", digest)
        except SeamlessException as e:
            print(e.message)

    def test_06_replace_object_with_package(self):
        OBJ_URL = "http://example.com/object/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": OBJ_URL}

        client = SWORD3Client(http=MockHttpLayer(200, BODY, HEADERS))

        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        with open(bag, "rb") as stream:
            try:
                dr = client.replace_object_with_package(
                    OBJ_URL,
                    stream,
                    "test.zip",
                    digest,
                    content_type="application/zip",
                    packaging=constants.PACKAGE_SWORDBAGIT,
                )
            except SeamlessException as e:
                print(e.message)
