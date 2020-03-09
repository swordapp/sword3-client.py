from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer

from sword3common import ByReference, ServiceDocument
from sword3common.test.fixtures import StatusFixtureFactory
from sword3common.exceptions import SeamlessException

import json


class TestService(TestCase):
    def test_01_create_object_by_reference(self):
        SD_URL = "http://example.com/service-document"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(201, BODY, HEADERS))

        br = ByReference()
        try:
            br.add_file("http://example.com/br/1.zip", "myfile.zip", "application/zip", True,
                    content_length=1000, ttl="2021-01-01T00:00:00Z")
        except SeamlessException as e:
            print(e.message)

        sd = ServiceDocument()
        sd.service_url = SD_URL

        try:
            dr = client.create_object_by_reference(sd, br)
        except SeamlessException as e:
            print(e.message)

    def test_02_append_by_reference(self):
        OBJ_URL = "http://example.com/obect/10"
        BODY = json.dumps(StatusFixtureFactory.status_document())
        HEADERS = {"Location": "http://example.com/location"}

        client = SWORD3Client(http=MockHttpLayer(200, BODY, HEADERS))

        br = ByReference()
        try:
            br.add_file("http://example.com/br/1.zip", "myfile.zip", "application/zip", True,
                        content_length=1000, ttl="2021-01-01T00:00:00Z")
        except SeamlessException as e:
            print(e.message)

        try:
            dr = client.append_by_reference(OBJ_URL, br)
        except SeamlessException as e:
            print(e.message)