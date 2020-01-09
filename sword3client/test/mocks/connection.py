from sword3client.connection import HttpLayer, HttpResponse
from sword3common.test.fixtures import ServiceFixtureFactory

import json

class MockHttpLayer(HttpLayer):
    def __init__(self, code=200, body=None, headers=None, stream=None):
        self.code = code
        self.body = body
        self.headers = headers
        self.stream = stream
        super(MockHttpLayer, self).__init__()

    def get(self, url, headers=None, stream=False):
        return self._respond()

    def post(self, url, body, headers=None):
        return self._respond()

    def put(self, url, body, headers=None):
        return self._respond()

    def delete(self, url):
        return self._respond()

    def _respond(self):
        body = self.body if self.body is not None else ""
        return MockHttpResponse(self.code, body, self.headers, self.stream)


class MockHttpResponse(HttpResponse):
    def __init__(self, status_code=None, body=None, headers=None, stream=None):
        self._status_code = status_code
        self._body = body
        self._headers = headers if headers is not None else {}
        self._stream = stream

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    @property
    def status_code(self):
        return self._status_code

    @property
    def body(self):
        return self._body

    @property
    def stream(self):
        return self._stream

    def header(self, header_name):
        return self._headers.get(header_name)


class HttpMockFactory(object):
    @classmethod
    def get_service(cls):
        status = 200
        body = json.dumps(ServiceFixtureFactory.service_document())
        return MockHttpLayer(status, body)