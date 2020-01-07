from sword3common.models.status import StatusDocument
from sword3common.lib.seamless import SeamlessException
from sword3client.exceptions import SWORD3InvalidDataFromServer

class DepositResponse(object):
    def __init__(self, status, location=None, data=None):
        self._status = status
        self._location = location
        if data is not None:
            try:
                self._status_document = StatusDocument(data)
            except SeamlessException as e:
                raise SWORD3InvalidDataFromServer(e, "DepositResponse could not be constructed as status document is invalid")

    @property
    def location(self):
        return self._location

    @property
    def status_code(self):
        return self._status

    @property
    def status_document(self):
        return self._status_document