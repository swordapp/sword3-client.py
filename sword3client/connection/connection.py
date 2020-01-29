class HttpLayer(object):
    def __init__(self, auth=None, headers=None):
        self._auth = auth
        self._headers = headers

    def get(self, url, headers=None, stream=False):
        raise NotImplementedError

    def put(self, url, data, headers=None):
        raise NotImplementedError

    def post(self, url, data, headers=None):
        raise NotImplementedError

    def delete(self, url):
        raise NotImplementedError


class HttpResponse(object):
    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError

    @property
    def status_code(self):
        raise NotImplementedError

    @property
    def body(self):
        raise NotImplementedError

    @property
    def stream(self):
        raise NotImplementedError

    def header(self, header_name):
        raise NotImplementedError
