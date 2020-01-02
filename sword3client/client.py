from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client import exceptions
from sword3client.models.deposit_response import DepositResponse

from sword3common.models.service import ServiceDocument
from sword3common.models.metadata import Metadata
from sword3common.lib.disposition import ContentDisposition
from sword3common import constants

import json
import hashlib
import base64
import typing

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
            digest[constants.DIGEST_SHA_256] = base64.b64encode(d.digest())

        digest_parts = []
        for k, v in digest.items():
            digest_parts.append("{x}={y}".format(x=k, y=v))
        digest_val = ", ".join(digest_parts)

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

    def create_object_with_binary(self,
                                  service: typing.Union[ServiceDocument, str],
                                  binary_stream: typing.IO,
                                  filename: str,
                                  digest: str,
                                  content_length: int=None,
                                  content_type: str=None,
                                  packaging: str=None
                                  ) -> DepositResponse:

        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = service
        if isinstance(service, ServiceDocument):
            service_url = service.service_url

        if content_type is None:
            content_type = "application/octet-stream"

        if packaging is None:
            packaging = constants.PACKAGE_BINARY

        headers = {
            "Content-Type": content_type,
            "Content-Disposition": ContentDisposition.binary_upload(filename).serialise(),
            "Digest": digest,
            "Packaging" : packaging,
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
            raise exceptions.SWORD3AuthenticationError(service_url, resp, "Authentication failed creating object with binary content")
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
            raise exceptions.SWORD3WireError(service_url, resp, "Unexpected status code; unable to create object with binary content")

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