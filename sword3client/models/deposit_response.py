class DepositResponse(object):
    def __init__(self, status, location, data):
        self._status = status
        self._location = location
        self._status_document = StatusDocument(data)
