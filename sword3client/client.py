from sword3client.connection.connection_requests import RequestsHttpLayer

from sword3common.models.service import ServiceDocument

import json

class SWORD3Client(object):

    def __init__(self, http=None):
        self._http = http if http is not None else RequestsHttpLayer()

    def get_service(self, service_url):
        resp = self._http.get(service_url)
        if resp.status_code == 200:
            data = json.loads(resp.body)
            return ServiceDocument(data)

    def create_object(self):
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