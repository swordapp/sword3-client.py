from sword3client.connection import HttpLayer, HttpResponse
from sword3common.test.fixtures import (
    ServiceFixtureFactory,
    StatusFixtureFactory,
    MetadataFixtureFactory,
    SegmentedUploadFixtureFactory
)

import json


class MockHttpLayer(HttpLayer):
    def __init__(self, code=200, body=None, headers=None, stream=None):
        self.code = code
        self.body = body
        self.headers = headers
        self.stream = stream
        super(MockHttpLayer, self).__init__()

    def get(self, url, headers=None, stream=False):
        return self._respond()

    def post(self, url, body, headers=None):
        return self._respond()

    def put(self, url, body, headers=None):
        return self._respond()

    def delete(self, url):
        return self._respond()

    def _respond(self):
        body = self.body if self.body is not None else ""
        return MockHttpResponse(self.code, body, self.headers, self.stream)


class MockHttpResponse(HttpResponse):
    def __init__(self, status_code=None, body=None, headers=None, stream=None):
        self._status_code = status_code
        self._body = body
        self._headers = headers if headers is not None else {}
        self._stream = stream

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    @property
    def status_code(self):
        return self._status_code

    @property
    def body(self):
        return self._body

    @property
    def stream(self):
        return self._stream

    def header(self, header_name):
        return self._headers.get(header_name)


class HttpMockFactory(object):
    @classmethod
    def get_service(cls):
        status = 200
        body = json.dumps(ServiceFixtureFactory.service_document())
        return MockHttpLayer(status, body)

    @classmethod
    def create_object_with_metadata(cls):
        status = 201
        body = json.dumps(StatusFixtureFactory.status_document())
        headers = {"Location": "http://example.com/object/10"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def create_object_with_binary(cls, links=None):
        status = 201
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def create_object_with_package(cls, links=None):
        status = 201
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def get_object(cls, links=None, not_found=False):
        if not_found:
            return MockHttpLayer(404)
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(status, body)

    @classmethod
    def get_metadata(cls, metadata=None):
        status = 200
        body = json.dumps(MetadataFixtureFactory.metadata())
        if metadata is not None:
            body = json.dumps(metadata.data)
        return MockHttpLayer(status, body)

    @classmethod
    def get_file(cls, stream):
        status = 200
        return MockHttpLayer(status, None, None, stream)

    @classmethod
    def append_metadata(cls):
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document())
        return MockHttpLayer(status, body)

    @classmethod
    def replace_metadata(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def add_binary(cls, links=None):
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10/file/binary1"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def add_package(cls, links=None):
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10/file/package1"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def replace_file(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def replace_fileset_with_binary(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def replace_object_with_metadata(cls, links=None):
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(status, body)

    @classmethod
    def replace_object_with_binary(cls, links=None):
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(status, body)

    @classmethod
    def replace_object_with_package(cls, links=None):
        status = 200
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(status, body)

    @classmethod
    def delete_metadata(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def delete_file(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def delete_fileset(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def delete_object(cls):
        status = 204
        return MockHttpLayer(status)

    @classmethod
    def create_object_by_reference(cls, links=None):
        status = 201
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def create_object_with_metadata_and_by_reference(cls, links=None):
        status = 201
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10"}
        return MockHttpLayer(status, body, headers)

    @classmethod
    def initialise_segmented_upload(cls):
        return MockHttpLayer(201, None, {"Location" : "http://example.com/temporary/1"})

    @classmethod
    def upload_file_segment(cls):
        return MockHttpLayer(204, None, None)

    @classmethod
    def segmented_upload_status(cls, received, expecting, size, segment_size):
        doc = SegmentedUploadFixtureFactory.segmented_upload_status(received, expecting, size, segment_size)
        return MockHttpLayer(200, json.dumps(doc), {"Content-Type" : "application/json"})

    @classmethod
    def abort_segmented_upload(cls):
        return MockHttpLayer(204, None, None)

    @classmethod
    def not_found(cls):
        return MockHttpLayer(404, None, None)

    @classmethod
    def method_not_allowed(cls):
        return MockHttpLayer(405, None, None)

    @classmethod
    def create_object_with_temporary_file(cls, links=None):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        headers = {"Location": "http://example.com/object/10"}
        return MockHttpLayer(201, body, headers)

    @classmethod
    def append_by_reference(cls, links=None):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(200, body, None)

    @classmethod
    def append_metadata_and_by_reference(cls, links=None):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(200, body, None)

    @classmethod
    def append_temporary_file(cls, links=None):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(200, body, None)

    @classmethod
    def replace_file_by_reference(cls):
        return MockHttpLayer(204, None, None)

    @classmethod
    def replace_file_with_temporary_file(cls):
        return MockHttpLayer(204, None, None)

    @classmethod
    def replace_fileset_by_reference(cls):
        return MockHttpLayer(204, None, None)

    @classmethod
    def replace_fileset_with_temporary_file(cls):
        return MockHttpLayer(204, None, None)

    @classmethod
    def replace_object_by_reference(cls, links):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(200, body, None)

    @classmethod
    def replace_object_with_metadata_and_by_reference(cls, links):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(200, body, None)

    @classmethod
    def replace_object_with_temporary_file(cls, links):
        body = json.dumps(StatusFixtureFactory.status_document(links))
        return MockHttpLayer(200, body, None)