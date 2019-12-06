from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client.exceptions import SWORD3WireError, SWORD3AuthenticationError, SWORD3NotFound

from sword3common.models.service import ServiceDocument

import json
import sys

class SWORD3Client(object):

    def __init__(self, http=None):
        self._http = http if http is not None else RequestsHttpLayer()

    def get_service(self, service_url):
        resp = self._http.get(service_url)
        if resp.status_code == 200:
            data = json.loads(resp.body)
            return ServiceDocument(data)
        elif resp.status_code == 401 or resp.status_code == 403:
            raise SWORD3AuthenticationError(service_url, resp, "Authentication failed retrieving service document")
        elif resp.status_code == 404:
            raise SWORD3NotFound(service_url, resp, "No Service Document found at requested URL")
        else:
            raise SWORD3WireError(service_url, resp, "Unexpected status code; unable to retrieve Service Document")

    def create_object_with_metadata(self, service, metadata, digest=None, metadata_format=None):
        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = service
        if isinstance(service, ServiceDocument):
            service_url = service.service_url

        body = json.dumps(metadata.data)
        content_length = sys.getsizeof(body)

        headers = {
            "Content-Type" : "application/json",
            "Content-Length" : content_length
        }


        self._http.post(service_url, body)

    def create_object_with_binary(self, service, binary, content_length=None, content_type=None, digest=None, packaging=None):
        pass

    def get_object(self):
        pass

    def add_to_object(self):
        pass

    def replace_object(self):
        pass

    def delete_object(self):
        pass

    def get_metadata(self):
        pass

    def replace_metadata(self):
        pass

    def replace_fileset(self):
        pass

    def delete_fileset(self):
        pass

    def get_file(self):
        pass

    def replace_file(self):
        pass

    def delete_file(self):
        pass