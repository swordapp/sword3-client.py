class HttpLayer(object):
    def __init__(self, auth=None):
        self._auth = auth

    def get(self, url):
        raise NotImplementedError

    def put(self):
        raise NotImplementedError

    def post(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError


class HttpResponse(object):
    @property
    def status_code(self):
        raise NotImplementedError

    @property
    def body(self):
        raise NotImplementedError