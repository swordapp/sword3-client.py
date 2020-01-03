class SWORD3Error(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class SWORD3WireError(SWORD3Error):
    def __init__(self, request_url, response, message):
        self.response = response
        self.request_url = request_url
        super(SWORD3WireError, self).__init__(message)

    def __str__(self):
        code = "unknown"
        if self.response is not None:
            code = str(self.response.status_code)
        request_on = "unknown"
        if self.request_url is not None:
            request_on = self.request_url
        return "[status: {x}] [request on: {z}] {y}".format(x=code, y=self.message, z=request_on)


class SWORD3AuthenticationError(SWORD3WireError):
    pass


class SWORD3NotFound(SWORD3WireError):
    pass


class SWORD3BadRequest(SWORD3WireError):
    pass


class SWORD3OperationNotAllowed(SWORD3WireError):
    pass


class SWORD3PreconditionFailed(SWORD3WireError):
    pass


class SWORD3MaxSizeExceeded(SWORD3WireError):
    pass


class SWORD3UnsupportedMediaType(SWORD3WireError):
    pass


class SWORD3InvalidDataFromServer(SWORD3Error):
    def __init__(self, inner, message):
        self.inner = inner
        super(SWORD3InvalidDataFromServer, self).__init__(message)

    def __str__(self):
        return "{x} -> {y}".format(x=self.message, y=self.inner.message)