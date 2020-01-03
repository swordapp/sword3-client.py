from sword3common.models.status import StatusDocument
from sword3common.lib.seamless import SeamlessException
from sword3client.exceptions import SWORD3InvalidDataFromServer

class DepositResponse(object):
    def __init__(self, status, location, data):
        self._status = status
        self._location = location
        try:
            self._status_document = StatusDocument(data)
        except SeamlessException as e:
            raise SWORD3InvalidDataFromServer(e, "DepositResponse could not be constructed as status document is invalid")

    def location(self):
        return self._location
