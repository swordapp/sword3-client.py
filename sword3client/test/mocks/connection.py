from sword3client.connection.connection import HttpLayer, HttpResponse


class MockHttpLayer(HttpLayer):
    def __init__(self, code=200, body=None, headers=None):
        self.code = code
        self.body = body
        self.headers = headers
        super(MockHttpLayer, self).__init__()

    def get(self, url, headers=None):
        return self._respond()

    def post(self, url, body, headers=None):
        return self._respond()

    def _respond(self):
        body = self.body if self.body is not None else ""
        return MockHttpResponse(self.code, body, self.headers)


class MockHttpResponse(HttpResponse):
    def __init__(self, status_code=None, body=None, headers=None):
        self._status_code = status_code
        self._body = body
        self._headers = headers if headers is not None else {}

    @property
    def status_code(self):
        return self._status_code

    @property
    def body(self):
        return self._body

    def header(self, header_name):
        return self._headers.get(header_name)
