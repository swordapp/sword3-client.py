from sword3client.connection.connection import HttpLayer, HttpResponse

from sword3common.test.fixtures.service import ServiceFixtureFactory

import json


class MockHttpLayer(HttpLayer):
    def __init__(self, code=200, body=True):
        self.code = code
        self.body = body
        super(MockHttpLayer, self).__init__()

    def get(self, url, headers=None):
        body = ""
        if self.body:
            body = json.dumps(ServiceFixtureFactory.service_document())
        return MockHttpResponse(self.code, body)


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
    