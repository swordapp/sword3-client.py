from unittest import TestCase

from sword3client.client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.exceptions import SWORD3WireError, SWORD3AuthenticationError, SWORD3NotFound

from sword3common.models.metadata import Metadata
from sword3common.test.fixtures.status import StatusFixtureFactory
from sword3common.lib.seamless import SeamlessException

import json

class TestService(TestCase):

    def test_01_create_object_with_metadata(self):

        SD_URL = "http://example.com/service-document"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location" : "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        try:
            dr = client.create_object_with_metadata(SD_URL, metadata)
        except SeamlessException as e:
            print(e.message)

