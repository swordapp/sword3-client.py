from unittest import TestCase

from sword3client.client import SWORD3Client
from sword3client.test.mocks.connection import MockHttpLayer

from sword3common.models.service import ServiceDocument

class TestService(TestCase):
    def test_01_get_service(self):
        client = SWORD3Client(http=MockHttpLayer())
        service = client.get_service("http://example.com/service-document")
        assert isinstance(service, ServiceDocument)
