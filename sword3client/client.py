from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client import exceptions
from sword3client.models.deposit_response import DepositResponse

from sword3common.models.service import ServiceDocument
from sword3common.models.metadata import Metadata
from sword3common.models.status import StatusDocument
from sword3common.lib.disposition import ContentDisposition
from sword3common import constants
from sword3common.lib.seamless import SeamlessException

import json
import hashlib
import base64
import typing
import contextlib

class SWORD3Client(object):

    def __init__(self, http=None):
        self._http = http if http is not None else RequestsHttpLayer()

    def get_service(self, service_url:str) -> ServiceDocument:
        resp = self._http.get(service_url)
        if resp.status_code == 200:
            data = json.loads(resp.body)
            return ServiceDocument(data)
        elif resp.status_code == 401 or resp.status_code == 403:
            raise exceptions.SWORD3AuthenticationError(service_url, resp, "Authentication failed retrieving service document")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(service_url, resp, "No Service Document found at requested URL")
        else:
            raise exceptions.SWORD3WireError(service_url, resp, "Unexpected status code; unable to retrieve Service Document")

    ######################################################
    ## Metadata protocol operations
    ######################################################

    def create_object_with_metadata(self,
                                    service: typing.Union[ServiceDocument, str],
                                    metadata: Metadata,
                                    digest: typing.Dict[str, str]=None,
                                    metadata_format: str=None
                                    ) -> DepositResponse:

        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = service
        if isinstance(service, ServiceDocument):
            service_url = service.service_url

        body = json.dumps(metadata.data)
        body_bytes = body.encode("utf-8")
        content_length = len(body_bytes)

        if digest is None:
            d = hashlib.sha256(body_bytes)
            digest = {
                constants.DIGEST_SHA_256: base64.b64encode(d.digest())
            }
        digest_val = self._make_digest_header(digest)

        if metadata_format is None:
            metadata_format = constants.URI_METADATA

        headers = {
            "Content-Type" : "application/json; charset=UTF-8",
            "Content-Length" : content_length,
            "Content-Disposition" : ContentDisposition.metadata_upload().serialise(),
            "Digest" : digest_val,
            "Metadata-Format" : metadata_format
        }

        resp = self._http.post(service_url, body_bytes, headers)

        if resp.status_code in [201, 202]:
            data = json.loads(resp.body)
            return DepositResponse(resp.status_code, resp.header("Location"), data)
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(service_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(service_url, resp, "Authentication failed creating object with metadata")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(service_url, resp, "No Service found at requested URL")
        elif resp.status_code == 405:
            raise exceptions.SWORD3OperationNotAllowed(service_url, resp, "The Service does not support deposit")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(service_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        elif resp.status_code == 413:
            raise exceptions.SWORD3MaxSizeExceeded(service_url, resp, "Your request exceeded the maximum deposit size for a single request against this server")
        elif resp.status_code == 415:
            raise exceptions.SWORD3UnsupportedMediaType(service_url, resp, "The Content-Type that you sent was not supported by the server")
        else:
            raise exceptions.SWORD3WireError(service_url, resp, "Unexpected status code; unable to create object with metadata")

    def get_metadata(self, status_or_metadata_url: typing.Union[ServiceDocument, str]) -> Metadata:
        metadata_url = status_or_metadata_url
        if isinstance(status_or_metadata_url, StatusDocument):
            metadata_url = status_or_metadata_url.metadata_url

        resp = self._http.get(metadata_url)

        if resp.status_code == 200:
            data = json.loads(resp.body)
            try:
                return Metadata(data)
            except SeamlessException as e:
                raise exceptions.SWORD3InvalidDataFromServer(e, "Metadata retrieval got invalid metadata document")
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(metadata_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(metadata_url, resp, "Authentication failed retrieving object metadata")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(metadata_url, resp, "No Metadata found at requested URL")
        elif resp.status_code == 405:
            raise exceptions.SWORD3OperationNotAllowed(metadata_url, resp, "The Object does not support metadata retrieval")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(metadata_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        else:
            raise exceptions.SWORD3WireError(metadata_url, resp, "Unexpected status code; unable to retrieve object metadata")

    def append_metadata(self,
                        status_or_object_url: typing.Union[ServiceDocument, str],
                        metadata: Metadata,
                        digest: typing.Dict[str, str]=None,
                        metadata_format: str=None
                        ) -> DepositResponse:

        object_url = status_or_object_url
        if isinstance(status_or_object_url, StatusDocument):
            object_url = status_or_object_url.object_url

        body = json.dumps(metadata.data)
        body_bytes = body.encode("utf-8")
        content_length = len(body_bytes)

        if digest is None:
            d = hashlib.sha256(body_bytes)
            digest = {
                constants.DIGEST_SHA_256: base64.b64encode(d.digest())
            }
        digest_val = self._make_digest_header(digest)

        if metadata_format is None:
            metadata_format = constants.URI_METADATA

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": content_length,
            "Content-Disposition": ContentDisposition.metadata_upload().serialise(),
            "Digest": digest_val,
            "Metadata-Format": metadata_format
        }

        resp = self._http.post(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            data = json.loads(resp.body)
            return DepositResponse(resp.status_code, resp.header("Location"), data)
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(object_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(object_url, resp, "Authentication failed appending metadata to object")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(object_url, resp, "No Object found at requested URL")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(object_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        elif resp.status_code == 413:
            raise exceptions.SWORD3MaxSizeExceeded(object_url, resp, "Your request exceeded the maximum deposit size for a single request against this server")
        elif resp.status_code == 415:
            raise exceptions.SWORD3UnsupportedMediaType(object_url, resp, "The Content-Type that you sent was not supported by the server")
        else:
            raise exceptions.SWORD3WireError(object_url, resp, "Unexpected status code; unable to append metadata to object")

    def replace_metadata(self,
                        status_or_metadata_url: typing.Union[ServiceDocument, str],
                        metadata: Metadata,
                        digest: typing.Dict[str, str]=None,
                        metadata_format: str=None
                        ) -> DepositResponse:

        metadata_url = status_or_metadata_url
        if isinstance(status_or_metadata_url, StatusDocument):
            metadata_url = status_or_metadata_url.metadata_url

        body = json.dumps(metadata.data)
        body_bytes = body.encode("utf-8")
        content_length = len(body_bytes)

        if digest is None:
            d = hashlib.sha256(body_bytes)
            digest = {
                constants.DIGEST_SHA_256: base64.b64encode(d.digest())
            }
        digest_val = self._make_digest_header(digest)

        if metadata_format is None:
            metadata_format = constants.URI_METADATA

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": content_length,
            "Content-Disposition": ContentDisposition.metadata_upload().serialise(),
            "Digest": digest_val,
            "Metadata-Format": metadata_format
        }

        resp = self._http.put(metadata_url, body, headers)

        if resp.status_code == 204:
            return DepositResponse(resp.status_code)
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(metadata_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(metadata_url, resp, "Authentication failed replacing metadata in object")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(metadata_url, resp, "No Metadata found at requested URL")
        elif resp.status_code == 405:
            raise exceptions.SWORD3OperationNotAllowed(metadata_url, resp, "The Object does not support metadata replacement")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(metadata_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        elif resp.status_code == 413:
            raise exceptions.SWORD3MaxSizeExceeded(metadata_url, resp, "Your request exceeded the maximum deposit size for a single request against this server")
        elif resp.status_code == 415:
            raise exceptions.SWORD3UnsupportedMediaType(metadata_url, resp, "The Content-Type that you sent was not supported by the server")
        else:
            raise exceptions.SWORD3WireError(metadata_url, resp, "Unexpected status code; unable to replace metadata in object")

    #######################################################
    # Binary/Package protocol operations
    #######################################################

    def create_object_with_binary(self,
                                  service: typing.Union[ServiceDocument, str],
                                  binary_stream: typing.IO,
                                  filename: str,
                                  digest: typing.Dict[str, str],
                                  content_length: int=None,
                                  content_type: str=None
                                  ) -> DepositResponse:

        return self._generic_create_binary(service, binary_stream, filename, digest, content_length, content_type,
                                           constants.PACKAGE_BINARY, ContentDisposition.binary_upload(filename), "binary")

    def create_object_with_package(self,
                                   service: typing.Union[ServiceDocument, str],
                                   binary_stream: typing.IO,
                                   filename: str,
                                   digest: typing.Dict[str, str],
                                   content_length: int=None,
                                   content_type: str=None,
                                   packaging: str=None
                                   ) -> DepositResponse:
        return self._generic_create_binary(service, binary_stream, filename, digest, content_length, content_type,
                                           packaging, ContentDisposition.package_upload(filename),
                                           "packaged")

    def add_binary(self,
                   status_or_object_url: typing.Union[StatusDocument, str],
                   binary_stream: typing.IO,
                   filename: str,
                   digest: typing.Dict[str, str],
                   content_length: int = None,
                   content_type: str = None
                   ) -> DepositResponse:

        return self._generic_add_binary(status_or_object_url, binary_stream, filename, digest, content_length, content_type,
                                        constants.PACKAGE_BINARY, ContentDisposition.binary_upload(filename), "binary")

    def add_package(self,
                    status_or_object_url: typing.Union[StatusDocument, str],
                    binary_stream: typing.IO,
                    filename: str,
                    digest: typing.Dict[str, str],
                    content_length: int = None,
                    content_type: str = None,
                    packaging: str=None
                    )-> DepositResponse:

        return self._generic_add_binary(status_or_object_url, binary_stream, filename, digest, content_length, content_type,
                                        packaging, ContentDisposition.package_upload(filename), "packaged")

    def _generic_create_binary(self,
                               service: typing.Union[ServiceDocument, str],
                               binary_stream: typing.IO,
                               filename: str,
                               digest: typing.Dict[str, str],
                               content_length: int,
                               content_type: str,
                               packaging: str,
                               content_disposition: ContentDisposition,
                               reporting_type: str
                               ) -> DepositResponse:
        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = service
        if isinstance(service, ServiceDocument):
            service_url = service.service_url

        if content_type is None:
            content_type = "application/octet-stream"

        if packaging is None:
            packaging = constants.PACKAGE_BINARY

        digest_val = self._make_digest_header(digest)

        headers = {
            "Content-Type": content_type,
            "Content-Disposition": content_disposition.serialise(),
            "Digest": digest_val,
            "Packaging": packaging,
        }

        if content_length is not None:
            headers["Content-Length"] = content_length

        resp = self._http.post(service_url, binary_stream, headers)

        if resp.status_code in [201, 202]:
            data = json.loads(resp.body)
            return DepositResponse(resp.status_code, resp.header("Location"), data)
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(service_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(service_url, resp, "Authentication failed creating object with {x} content".format(x=reporting_type))
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(service_url, resp, "No Service found at requested URL")
        elif resp.status_code == 405:
            raise exceptions.SWORD3OperationNotAllowed(service_url, resp, "The Service does not support deposit")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(service_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        elif resp.status_code == 413:
            raise exceptions.SWORD3MaxSizeExceeded(service_url, resp, "Your request exceeded the maximum deposit size for a single request against this server")
        elif resp.status_code == 415:
            raise exceptions.SWORD3UnsupportedMediaType(service_url, resp, "The Content-Type that you sent was not supported by the server")
        else:
            raise exceptions.SWORD3WireError(service_url, resp, "Unexpected status code; unable to create object with {x} content".format(x=reporting_type))

    def _generic_add_binary(self,
                            status_or_object_url: typing.Union[StatusDocument, str],
                            binary_stream: typing.IO,
                            filename: str,
                            digest: typing.Dict[str, str],
                            content_length: int,
                            content_type: str,
                            packaging: str,
                            content_disposition: ContentDisposition,
                            reporting_type: str
                            ) -> DepositResponse:

        object_url = status_or_object_url
        if isinstance(status_or_object_url, StatusDocument):
            object_url = status_or_object_url.object_url

        if content_type is None:
            content_type = "application/octet-stream"

        if packaging is None:
            packaging = constants.PACKAGE_BINARY

        digest_val = self._make_digest_header(digest)

        headers = {
            "Content-Type": content_type,
            "Content-Disposition": content_disposition.serialise(),
            "Digest": digest_val,
            "Packaging": packaging,
        }

        if content_length is not None:
            headers["Content-Length"] = content_length

        resp = self._http.post(object_url, binary_stream, headers)

        if resp.status_code in [200, 202]:
            data = json.loads(resp.body)
            return DepositResponse(resp.status_code, resp.header("Location"), data)
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(object_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(object_url, resp, "Authentication failed appending to object with {x} content".format(x=reporting_type))
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(object_url, resp, "No Object found at requested URL")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(object_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        elif resp.status_code == 413:
            raise exceptions.SWORD3MaxSizeExceeded(object_url, resp, "Your request exceeded the maximum deposit size for a single request against this server")
        elif resp.status_code == 415:
            raise exceptions.SWORD3UnsupportedMediaType(object_url, resp, "The Content-Type that you sent was not supported by the server")
        else:
            raise exceptions.SWORD3WireError(object_url, resp, "Unexpected status code; unable to append to object with {x} content".format(x=reporting_type))


    #####################################################
    ## Object level protocol operations
    #####################################################

    def get_object(self, sword_object: typing.Union[StatusDocument, str]) -> StatusDocument:
        # get the status url.  The first argument may be the URL or the StatusDocument
        object_url = sword_object
        if isinstance(sword_object, StatusDocument):
            object_url = sword_object.object_url

        resp = self._http.get(object_url)

        if resp.status_code == 200:
            data = json.loads(resp.body)
            try:
                return StatusDocument(data)
            except SeamlessException as e:
                raise exceptions.SWORD3InvalidDataFromServer(e, "Object retrieval got invalid status document")
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(object_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(object_url, resp, "Authentication failed retrieving an object")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(object_url, resp, "No Object found at requested URL")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(object_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        else:
            raise exceptions.SWORD3WireError(object_url, resp, "Unexpected status code; unable to retrieve object")

    #################################################
    ## Individual file protocol operations
    #################################################

    def get_file(self, file_url: str):
        @contextlib.contextmanager
        def file_getter():
            resp = self._http.get(file_url, stream=True)
            resp.__enter__()

            if resp.status_code == 400:
                raise exceptions.SWORD3BadRequest(file_url, resp, "The server did not understand the request")
            elif resp.status_code in [401, 403]:
                raise exceptions.SWORD3AuthenticationError(file_url, resp, "Authentication failed retrieving object metadata")
            elif resp.status_code == 404:
                raise exceptions.SWORD3NotFound(file_url, resp, "No File found at requested URL")
            elif resp.status_code == 405:
                raise exceptions.SWORD3OperationNotAllowed(file_url, resp, "The Object does not support file retrieval")
            elif resp.status_code == 412:
                raise exceptions.SWORD3PreconditionFailed(file_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
            elif resp.status_code != 200:
                raise exceptions.SWORD3WireError(file_url, resp, "Unexpected status code; unable to retrieve file")

            yield resp.stream
            resp.__exit__()

        return file_getter()

    def replace_file(self,
                     file_url: str,
                     binary_stream: typing.IO,
                     content_type: str,
                     digest: typing.Dict[str, str],
                     filename: str=None):

        digest_val = self._make_digest_header(digest)

        # FIXME: an issue has been raised for this - what happens if no filename is provided
        if filename is None:
            filename = "untitled"

        headers = {
            "Content-Type": content_type,
            "Content-Disposition": ContentDisposition.binary_upload(filename).serialise(),
            "Digest": digest_val,
            "Packaging": constants.PACKAGE_BINARY,
        }

        resp = self._http.put(file_url, binary_stream, headers)

        if resp.status_code == 204:
            return DepositResponse(resp.status_code)
        elif resp.status_code == 400:
            raise exceptions.SWORD3BadRequest(file_url, resp, "The server did not understand the request")
        elif resp.status_code in [401, 403]:
            raise exceptions.SWORD3AuthenticationError(file_url, resp, "Authentication failed replacing file")
        elif resp.status_code == 404:
            raise exceptions.SWORD3NotFound(file_url, resp, "No File found at requested URL")
        elif resp.status_code == 405:
            raise exceptions.SWORD3OperationNotAllowed(file_url, resp, "The Object does not support file replacement")
        elif resp.status_code == 412:
            raise exceptions.SWORD3PreconditionFailed(file_url, resp, "Your request could not be processed as-is, there may be inconsistencies in your request parameters")
        elif resp.status_code == 413:
            raise exceptions.SWORD3MaxSizeExceeded(file_url, resp, "Your request exceeded the maximum deposit size for a single request against this server")
        else:
            raise exceptions.SWORD3WireError(file_url, resp, "Unexpected status code; unable to replace file on object")

    def add_to_object(self):
        pass

    def replace_object(self):
        pass

    def delete_object(self):
        pass

    def replace_fileset(self):
        pass

    def delete_fileset(self):
        pass


    def delete_file(self):
        pass

    ###########################################################
    ## Utility methods
    ###########################################################

    def _make_digest_header(self, digest: typing.Dict[str, str]):
        digest_parts = []
        for k, v in digest.items():
            digest_parts.append("{x}={y}".format(x=k, y=v))
        return ", ".join(digest_parts)