from sword3client.connection.connection import HttpLayer, HttpResponse

from sword3common.test.fixtures.service import ServiceFixtureFactory

import json

class MockHttpLayer(HttpLayer):
    def get(self, url):
        body = ServiceFixtureFactory.service_document()
        return MockHttpResponse(200, json.dumps(body))


class MockHttpResponse(HttpResponse):
    def __init__(self, status_code=None, body=None):
        self._status_code = status_code
        self._body = body

    @property
    def status_code(self):
        return self._status_code

    @property
    def body(self):
        return self._body