from sword3client.connection.connection import HttpLayer, HttpResponse

# Make this package the canonical "import from" location
HttpLayer.__module__ = __name__
HttpResponse.__module__ = __name__

__all__ = ['HttpLayer', 'HttpResponse']