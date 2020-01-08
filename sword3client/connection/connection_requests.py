from sword3client.connection import HttpLayer, HttpResponse
import requests


class RequestsHttpLayer(HttpLayer):
    def __init__(self, auth=None):
        super(RequestsHttpLayer, self).__init__(auth)

    def get(self, url, headers=None, stream=False):
        return RequestsHttpResponse(requests.get(url, stream=stream, headers=headers))

    def put(self, url, data, headers=None):
        return RequestsHttpResponse(requests.put(url, data, headers=headers))

    def post(self, url, data, headers=None):
        return RequestsHttpResponse(requests.post(url, data, headers=headers))

    def delete(self, url):
        return RequestsHttpResponse(requests.delete(url))


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