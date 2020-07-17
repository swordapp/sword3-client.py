from sword3client.models.sword_response import SWORDResponse
from sword3client.client import SWORD3Client

# Make this package the canonical "import from" location
SWORDResponse.__module__ = __name__
SWORD3Client.__module__ = __name__

__all__ = ['SWORD3Client', 'SWORDResponse']