from sword3client.connection.connection import HttpLayer, HttpResponse
import requests


class RequestsHttpLayer(HttpLayer):
    def __init__(self, auth=None):
        super(RequestsHttpLayer, self).__init__(auth)

    def get(self, url, headers=None):
        return RequestsHttpResponse(requests.get(url, headers=headers))

    def put(self):
        pass

    def post(self, url, data, headers=None):
        return RequestsHttpResponse(requests.post(url, data, headers=headers))

    def delete(self):
        pass


class RequestsHttpResponse(HttpResponse):
    def __init__(self, resp):
        self.resp = resp

    @property
    def status_code(self):
        return self.resp.status_code

    @property
    def body(self):
        return self.resp.text

    def header(self, header_name):
        return self.resp.headers.get(header_name)