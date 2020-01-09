from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client.test.mocks.connection import HttpMockFactory

from sword3common import constants, Metadata

from io import BytesIO
import hashlib
import base64

SERVICE_URL = "http://localhost:8000/service-document"
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
        sd = client.get_service(SERVICE_URL)
        sd.verify_against_struct()

    def test_02_create_and_retrieve_with_metadata(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata)

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Retrieve the object itself
        client.set_http_layer(HTTP_FACTORY.get_object())
        status2 = client.get_object(status)
        status2.verify_against_struct()
        assert status.data == status2.data
        assert status.metadata_url is not None

        # 3. Retrieve the metadata back
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata))
        metadata2 = client.get_metadata(status2)
        metadata2.verify_against_struct()
        assert metadata.get_dc_field("creator") == metadata2.get_dc_field("creator")
        assert metadata.get_dcterms_field("rights") == metadata2.get_dcterms_field("rights")
        assert metadata.get_field("custom") == metadata2.get_field("custom")

    def test_01_create_object_with_binary(self):
        client = SWORD3Client()

        bytes = b"this is a random stream of bytes"
        d = hashlib.sha256(bytes)
        digest = "{x}={y}".format(x=constants.DIGEST_SHA_256, y=base64.b64encode(d.digest()))
        stream = BytesIO(bytes)

        dr = client.create_object_with_binary(SD_URL, stream, "test.bin", digest)
        print(dr.location)
