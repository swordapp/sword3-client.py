from sword3common.models.status import StatusDocument
from sword3common import exceptions

import json


class SWORDResponse(object):
    """Class to wrap the HTTP response for a SWORD request, to give you some convenient semantic APIs"""
    def __init__(self, http_response):
        self._http_response = http_response
        self._status_document = None

        body = http_response.body
        if body:
            data = json.loads(body)
            try:
                self._status_document = StatusDocument(data)
            except exceptions.SeamlessException as e:
                raise exceptions.InvalidDataFromServer(
                    "DepositResponse could not be constructed as status document is invalid"
                ) from e

    @property
    def location(self):
        """Get the location of the resource created by the request operation that you issued"""
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
        """HTTP status code of the response"""
        return self._http_response.status_code

    @property
    def status_document(self):
        """The Status Document object if present for this response"""
        return self._status_document
