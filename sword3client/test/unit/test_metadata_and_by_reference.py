from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.exceptions import (
    SWORD3AuthenticationError,
    SWORD3NotFound,
    SWORD3WireError,
)

from sword3common import Metadata, ByReference, MetadataAndByReference, ServiceDocument
from sword3common.test.fixtures import StatusFixtureFactory, MetadataFixtureFactory
from sword3common.exceptions import SeamlessException

import json


class TestService(TestCase):
    def test_01_create_object_with_metadata_and_by_reference(self):

        SD_URL = "http://example.com/service-document"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        br = ByReference()
        try:
            br.add_file("http://example.com/br/1.zip", "myfile.zip", "application/zip", True,
                        content_length=1000, ttl="2021-01-01T00:00:00Z")
        except SeamlessException as e:
            print(e.message)

        mdbr = MetadataAndByReference(metadata, br)

        sd = ServiceDocument()
        sd.service_url = SD_URL

        try:
            dr = client.create_object_with_metadata_and_by_reference(sd, mdbr)
        except SeamlessException as e:
            print(e.message)