from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client.test.mocks.connection import HttpMockFactory

from sword3common import constants

from io import BytesIO
import hashlib
import base64

SD_URL = "http://localhost:8000/service-document"
DEPOSIT_URL = "http://localhost:8000/api/deposit"

AUTH_TOKEN = ""
INVENIO_HTTP_LAYER = RequestsHttpLayer(headers={'Authorization': 'Bearer ' + AUTH_TOKEN})
MOCK_MODE = True

class HttpLayerFactory(object):
    def __init__(self, default, use_mock):
        self._default = default
        self._use_mock = use_mock

    def __getattr__(self, item):
        if hasattr(self.__class__, item):
            return object.__getattribute__(self, item)

        if not self._use_mock:
            return self._default

        return getattr(HttpMockFactory, item)

HTTP_FACTORY = HttpLayerFactory(INVENIO_HTTP_LAYER, MOCK_MODE)

class TestInvenio(TestCase):

    def test_01_service_document(self):
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SD_URL)
        sd.verify_against_struct()

    def test_01_create_object_with_binary(self):
        client = SWORD3Client()

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = "{x}={y}".format(x=constants.DIGEST_SHA_256, y=base64.b64encode(d.digest()))
        stream = BytesIO(bytes)

        dr = client.create_object_with_binary(SD_URL, stream, "test.bin", digest)
        print(dr.location)
