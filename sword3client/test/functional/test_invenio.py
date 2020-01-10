from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client.test.mocks.connection import HttpMockFactory
from sword3client.lib import paths

from sword3common import constants, Metadata

from io import BytesIO
import hashlib
import base64
import os
import shutil

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
            return self.get_default

        return getattr(HttpMockFactory, item)

    def get_default(self, *args, **kwargs):
        return self._default

HTTP_FACTORY = HttpLayerFactory(INVENIO_HTTP_LAYER, MOCK_MODE)

class TestInvenio(TestCase):

    def setUp(self) -> None:
        self.tmpFiles = []

    def tearDown(self) -> None:
        for tmpFile in self.tmpFiles:
            path = paths.rel2abs(__file__, "..", "tmp", tmpFile)
            if os.path.exists(path):
                os.remove(path)

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

    def test_03_create_object_with_binary(self):
        # 1. Create the object with a binary stream
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {
            constants.DIGEST_SHA_256: d.digest()
        }
        stream = BytesIO(bytes)

        client = SWORD3Client(HTTP_FACTORY.create_object_with_binary(links=[
            {
                "@id": "http://example.com/object/10/test.bin",
                "rel": [constants.REL_ORIGINAL_DEPOSIT],
                "contentType": "text/plain",
                "packaging": "http://purl.org/net/sword/3.0/package/Binary"
            },
        ]))
        dr = client.create_object_with_binary(SERVICE_URL, stream, "test.bin", digest, content_length, content_type="text/plain")

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Download the file
        links = status.links
        assert len(links) == 1
        link = links[0]

        assert "@id" in link
        assert constants.REL_ORIGINAL_DEPOSIT in link.get("rel")
        assert link.get("contentType") == "text/plain"

        url = link.get("@id")
        client.set_http_layer(HTTP_FACTORY.get_file(BytesIO(bytes)))
        with client.get_file(url) as download:
            received = download.read()
        assert received == bytes

    def test_04_create_object_with_package(self):
        # 1. Create the object with a package
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {
            constants.DIGEST_SHA_256: base64.b64encode(d.digest())
        }
        file_size = os.path.getsize(bag)

        client = SWORD3Client(HTTP_FACTORY.create_object_with_package(links=[
            {
                "@id": "http://example.com/object/10/test.zip",
                "rel": [constants.REL_ORIGINAL_DEPOSIT],
                "contentType": "application/zip",
                "packaging": constants.PACKAGE_SWORDBAGIT
            },
        ]))

        with open(bag, "rb") as stream:
            dr = client.create_object_with_package(SERVICE_URL, stream, "test.zip", digest,
                                                   content_type="application/zip",
                                                   content_length=file_size,
                                                   packaging=constants.PACKAGE_SWORDBAGIT)

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Download the zip
        assert len(status.links) >= 1
        ods = status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])
        assert len(ods) == 1
        link = ods[0]

        assert "@id" in link
        assert "http://purl.org/net/sword/3.0/terms/originalDeposit" in link.get("rel")
        assert link.get("contentType") == "application/zip"

        filename = "test_invenio.test_04_create_object_with_package.zip"
        self.tmpFiles.append(filename)

        url = link.get("@id")
        data_out = paths.rel2abs(__file__, "..", "tmp", filename)
        with open(bag, "rb") as stream:
            client.set_http_layer(HTTP_FACTORY.get_file(stream))
            with client.get_file(url) as download:
                with open(data_out, 'wb') as g:
                    shutil.copyfileobj(download, g)

        d2 = paths.sha256(data_out)
        assert d.hexdigest() == d2.hexdigest()