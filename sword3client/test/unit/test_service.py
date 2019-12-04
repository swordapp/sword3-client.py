from unittest import TestCase

from sword3client.client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer
from sword3client.exceptions import SWORD3WireError, SWORD3AuthenticationError, SWORD3NotFound

from sword3common.models.service import ServiceDocument

class TestService(TestCase):

    def test_01_get_service(self):

        SD_URL = "http://example.com/service-document"

        client = SWORD3Client(http=MockHttpLayer(200, True))
        service = client.get_service(SD_URL)
        assert isinstance(service, ServiceDocument)

        client = SWORD3Client(http=MockHttpLayer(401, False))
        with self.assertRaises(SWORD3AuthenticationError):
            try:
                service = client.get_service(SD_URL)
            except SWORD3AuthenticationError as e:
                assert e.request_url == SD_URL
                assert e.response is not None
                assert e.message is not None
                raise

        client = SWORD3Client(http=MockHttpLayer(403, False))
        with self.assertRaises(SWORD3AuthenticationError):
            service = client.get_service(SD_URL)

        client = SWORD3Client(http=MockHttpLayer(404, False))
        with self.assertRaises(SWORD3NotFound):
            service = client.get_service(SD_URL)

        client = SWORD3Client(http=MockHttpLayer(405, False))
        with self.assertRaises(SWORD3WireError):
            service = client.get_service(SD_URL)