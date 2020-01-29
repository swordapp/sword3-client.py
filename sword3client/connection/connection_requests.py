from sword3client.connection import HttpLayer, HttpResponse
import requests


class RequestsHttpLayer(HttpLayer):
    def __init__(self, auth=None, headers=None):
        super(RequestsHttpLayer, self).__init__(auth, headers)

    def get(self, url, headers=None, stream=False):
        headers = self._get_headers(headers)
        return RequestsHttpResponse(requests.get(url, stream=stream, headers=headers))

    def put(self, url, data, headers=None):
        headers = self._get_headers(headers)
        return RequestsHttpResponse(requests.put(url, data, headers=headers))

    def post(self, url, data, headers=None):
        headers = self._get_headers(headers)
        return RequestsHttpResponse(requests.post(url, data, headers=headers))

    def delete(self, url):
        headers = self._get_headers(None)
        return RequestsHttpResponse(requests.delete(url, headers=headers))

    def _get_headers(self, headers):
        if headers is None and self._headers is None:
            return None
        if headers is None:
            return self._headers
        if self._headers is None:
            return headers
        headers.update(self._headers)
        return headers


class RequestsHttpResponse(HttpResponse):
    def __init__(self, resp):
        self.resp = resp

    def __enter__(self):
        self.resp.__enter__()

    def __exit__(self):
        self.resp.__exit__()

    @property
    def status_code(self):
        return self.resp.status_code

    @property
    def body(self):
        return self.resp.text

    @property
    def stream(self):
        return self.resp.raw

    def header(self, header_name):
        return self.resp.headers.get(header_name)
