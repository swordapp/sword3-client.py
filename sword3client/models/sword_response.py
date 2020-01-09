from sword3common.models.status import StatusDocument
from sword3common.lib.seamless import SeamlessException
from sword3client.exceptions import SWORD3InvalidDataFromServer

import json

class SWORDResponse(object):
    def __init__(self, http_response):
        self._http_response = http_response
        body = http_response.body
        if body:
            data = json.loads(body)
            try:
                self._status_document = StatusDocument(data)
            except SeamlessException as e:
                raise SWORD3InvalidDataFromServer(e, "DepositResponse could not be constructed as status document is invalid")

    @property
    def location(self):
        # first look in the http response
        http_location = self._http_response.header("Location")
        if http_location is not None:
            return http_location

        # then look in the status document
        if self._status_document is not None:
            return self._status_document.object_url

        # otherwise we weren't given one
        return None

    @property
    def status_code(self):
        return self._http_response.status_code

    @property
    def status_document(self):
        return self._status_document