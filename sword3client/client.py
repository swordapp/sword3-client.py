from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client import SWORDResponse, exceptions

from sword3common import (
    ServiceDocument,
    Metadata,
    StatusDocument,
    ContentDisposition,
    ByReference,
    constants,
)
from sword3common import exceptions as common_exceptions

import json
import hashlib
import base64
import typing
import contextlib


class SWORD3Client(object):
    def __init__(self, http=None):
        self._http = http if http is not None else RequestsHttpLayer()

    def set_http_layer(self, http):
        self._http = http

    def get_service(self, service_url: str) -> ServiceDocument:
        resp = self._http.get(service_url)
        if resp.status_code == 200:
            data = json.loads(resp.body)
            return ServiceDocument(data)
        else:
            self._raise_for_status_code(resp, service_url, [401, 403, 404])

    ######################################################
    ## Metadata protocol operations
    ######################################################

    def create_object_with_metadata(
        self,
        service: typing.Union[ServiceDocument, str],
        metadata: Metadata,
        digest: typing.Dict[str, str] = None,
        metadata_format: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = self._get_url(service, "service_url")
        body_bytes, headers = self._metadata_deposit_properties(
            metadata, metadata_format, digest, in_progress=in_progress
        )
        resp = self._http.post(service_url, body_bytes, headers)

        if resp.status_code in [201, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, service_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def replace_object_with_metadata(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        metadata: Metadata,
        digest: typing.Dict[str, str] = None,
        metadata_format: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        object_url = self._get_url(status_or_object_url, "object_url")
        body_bytes, headers = self._metadata_deposit_properties(
            metadata, metadata_format, digest, in_progress=in_progress
        )
        resp = self._http.put(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def get_metadata(
        self, status_or_metadata_url: typing.Union[StatusDocument, str]
    ) -> Metadata:

        metadata_url = self._get_url(status_or_metadata_url, "metadata_url")
        resp = self._http.get(metadata_url)

        if resp.status_code == 200:
            data = json.loads(resp.body)
            try:
                return Metadata(data)
            except common_exceptions.SeamlessException as e:
                raise exceptions.SWORD3InvalidDataFromServer(
                    e, "Metadata retrieval got invalid metadata document"
                )
        else:
            self._raise_for_status_code(
                resp, metadata_url, [400, 401, 403, 404, 405, 412]
            )

    def append_metadata(
        self,
        status_or_object_url: typing.Union[ServiceDocument, str],
        metadata: Metadata,
        digest: typing.Dict[str, str] = None,
        metadata_format: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        object_url = self._get_url(status_or_object_url, "object_url")
        body_bytes, headers = self._metadata_deposit_properties(
            metadata, metadata_format, digest, in_progress=in_progress,
        )
        resp = self._http.post(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 412, 413, 415]
            )

    def replace_metadata(
        self,
        status_or_metadata_url: typing.Union[ServiceDocument, str],
        metadata: Metadata,
        digest: typing.Dict[str, str] = None,
        metadata_format: str = None,
    ) -> SWORDResponse:

        metadata_url = self._get_url(status_or_metadata_url, "metadata_url")
        body_bytes, headers = self._metadata_deposit_properties(
            metadata, metadata_format, digest
        )
        resp = self._http.put(metadata_url, body_bytes, headers)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, metadata_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def delete_metadata(
        self, status_or_metadata_url: typing.Union[ServiceDocument, str]
    ) -> SWORDResponse:

        metadata_url = self._get_url(status_or_metadata_url, "metadata_url")
        resp = self._http.delete(metadata_url)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, metadata_url, [400, 401, 403, 404, 405, 412, 413]
            )

    def _metadata_deposit_properties(
        self, metadata, metadata_format, digest, in_progress: bool = None,
    ):
        body = json.dumps(metadata.data)
        body_bytes = body.encode("utf-8")
        content_length = len(body_bytes)

        if digest is None:
            d = hashlib.sha256(body_bytes)
            digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        digest_val = self._make_digest_header(digest)

        if metadata_format is None:
            metadata_format = constants.URI_METADATA

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": content_length,
            "Content-Disposition": ContentDisposition.metadata_upload().serialise(),
            "Digest": digest_val,
            "Metadata-Format": metadata_format,
        }

        if in_progress is not None:
            headers["In-Progress"] = "true" if in_progress else "false"

        return body_bytes, headers

    #######################################################
    # Binary/Package protocol operations
    #######################################################

    def create_object_with_binary(
        self,
        service: typing.Union[ServiceDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        return self._generic_create_binary(
            service,
            binary_stream,
            digest,
            content_length,
            content_type,
            constants.PACKAGE_BINARY,
            ContentDisposition.binary_upload(filename),
            in_progress=in_progress,
        )

    def create_object_with_package(
        self,
        service: typing.Union[ServiceDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
        packaging: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:
        return self._generic_create_binary(
            service,
            binary_stream,
            digest,
            content_length,
            content_type,
            packaging,
            ContentDisposition.package_upload(filename),
            in_progress=in_progress,
        )

    def add_binary(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        return self._generic_add_binary(
            status_or_object_url,
            binary_stream,
            digest,
            content_length,
            content_type,
            constants.PACKAGE_BINARY,
            ContentDisposition.binary_upload(filename),
            in_progress=in_progress,
        )

    def add_package(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
        packaging: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        return self._generic_add_binary(
            status_or_object_url,
            binary_stream,
            digest,
            content_length,
            content_type,
            packaging,
            ContentDisposition.package_upload(filename),
            in_progress=in_progress,
        )

    def replace_object_with_binary(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        return self._generic_replace_binary(
            status_or_object_url,
            binary_stream,
            digest,
            content_length,
            content_type,
            constants.PACKAGE_BINARY,
            ContentDisposition.binary_upload(filename),
            in_progress=in_progress,
        )

    def replace_object_with_package(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
        packaging: str = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        return self._generic_replace_binary(
            status_or_object_url,
            binary_stream,
            digest,
            content_length,
            content_type,
            packaging,
            ContentDisposition.package_upload(filename),
            in_progress=in_progress,
        )

    def _generic_create_binary(
        self,
        service: typing.Union[ServiceDocument, str],
        binary_stream: typing.IO,
        digest: typing.Dict[str, str],
        content_length: int,
        content_type: str,
        packaging: str,
        content_disposition: ContentDisposition,
        in_progress: bool,
    ) -> SWORDResponse:

        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = self._get_url(service, "service_url")
        headers = self._binary_deposit_properties(
            content_type,
            packaging,
            digest,
            content_disposition,
            content_length,
            in_progress=in_progress,
        )
        resp = self._http.post(service_url, binary_stream, headers)

        if resp.status_code in [201, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, service_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def _generic_add_binary(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        digest: typing.Dict[str, str],
        content_length: int,
        content_type: str,
        packaging: str,
        content_disposition: ContentDisposition,
        in_progress: bool,
    ) -> SWORDResponse:

        object_url = self._get_url(status_or_object_url, "object_url")
        headers = self._binary_deposit_properties(
            content_type,
            packaging,
            digest,
            content_disposition,
            content_length,
            in_progress=in_progress,
        )
        resp = self._http.post(object_url, binary_stream, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 412, 413, 415]
            )

    def _generic_replace_binary(
        self,
        status_or_object_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        digest: typing.Dict[str, str],
        content_length: int,
        content_type: str,
        packaging: str,
        content_disposition: ContentDisposition,
        in_progress: bool,
    ) -> SWORDResponse:

        object_url = self._get_url(status_or_object_url, "object_url")
        headers = self._binary_deposit_properties(
            content_type,
            packaging,
            digest,
            content_disposition,
            content_length,
            in_progress=in_progress,
        )
        resp = self._http.put(object_url, binary_stream, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 412, 413, 415]
            )

    def _binary_deposit_properties(
        self,
        content_type,
        packaging,
        digest,
        content_disposition,
        content_length,
        in_progress: bool = None,
    ):
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
            headers["Content-Length"] = str(content_length)

        if in_progress is not None:
            headers["In-Progress"] = "true" if in_progress else "false"

        return headers

    #####################################################
    ## By-Reference Operations
    #####################################################

    def create_object_by_reference(
        self,
        service: typing.Union[ServiceDocument, str],
        by_reference: ByReference,
        digest: typing.Dict[str, str] = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = self._get_url(service, "service_url")
        body_bytes, headers = self._by_reference_deposit_properties(
            by_reference, digest, in_progress=in_progress
        )
        resp = self._http.post(service_url, body_bytes, headers)

        if resp.status_code in [201, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, service_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def _by_reference_deposit_properties(
        self, by_reference, digest, in_progress: bool = None,
    ):
        body = json.dumps(by_reference.data)
        body_bytes = body.encode("utf-8")
        content_length = len(body_bytes)

        if digest is None:
            d = hashlib.sha256(body_bytes)
            digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        digest_val = self._make_digest_header(digest)

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": content_length,
            "Content-Disposition": ContentDisposition.by_reference_upload().serialise(),
            "Digest": digest_val
        }

        if in_progress is not None:
            headers["In-Progress"] = "true" if in_progress else "false"

        return body_bytes, headers

    #####################################################
    ## Object level protocol operations
    #####################################################

    def get_object(
        self, sword_object: typing.Union[StatusDocument, str]
    ) -> StatusDocument:
        # get the status url.  The first argument may be the URL or the StatusDocument
        object_url = self._get_url(sword_object, "object_url")
        resp = self._http.get(object_url)

        if resp.status_code == 200:
            data = json.loads(resp.body)
            try:
                return StatusDocument(data)
            except common_exceptions.SeamlessException as e:
                raise exceptions.SWORD3InvalidDataFromServer(
                    e, "Object retrieval got invalid status document"
                )
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 410, 412]
            )

    def delete_object(
        self, sword_object: typing.Union[StatusDocument, str]
    ) -> SWORDResponse:

        object_url = self._get_url(sword_object, "object_url")
        resp = self._http.delete(object_url)

        if resp.status_code in [202, 204]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 405, 412]
            )

    #################################################
    ## Individual file protocol operations
    #################################################

    def get_file(self, file_url: str):
        @contextlib.contextmanager
        def file_getter():
            resp = self._http.get(file_url, stream=True)
            resp.__enter__()

            self._raise_for_status_code(
                resp, file_url, [400, 401, 403, 404, 405, 412], False
            )
            if resp.status_code != 200:
                raise exceptions.SWORD3WireError(
                    file_url, resp, "Unexpected status code; unable to retrieve file"
                )

            yield resp.stream
            resp.__exit__()

        return file_getter()

    def replace_file(
        self,
        file_url: str,
        binary_stream: typing.IO,
        content_type: str,
        digest: typing.Dict[str, str],
        filename: str = "untitled",  # FIXME: an issue has been raised for this - what happens if no filename is provided
        content_length: int = None,
    ):

        headers = self._binary_deposit_properties(
            content_type,
            constants.PACKAGE_BINARY,
            digest,
            ContentDisposition.binary_upload(filename),
            content_length,
        )

        resp = self._http.put(file_url, binary_stream, headers)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, file_url, [400, 401, 403, 404, 405, 412, 413]
            )

    def delete_file(self, file_url: str):
        resp = self._http.delete(file_url)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(resp, file_url, [400, 401, 403, 404, 405, 412])

    ###########################################################
    ## Fileset protocol operations
    ###########################################################

    def replace_fileset_with_binary(
        self,
        status_or_fileset_url: typing.Union[StatusDocument, str],
        binary_stream: typing.IO,
        filename: str,
        digest: typing.Dict[str, str],
        content_length: int = None,
        content_type: str = None,
    ) -> SWORDResponse:
        fileset_url = self._get_url(status_or_fileset_url, "fileset_url")
        headers = self._binary_deposit_properties(
            content_type,
            None,
            digest,
            ContentDisposition.binary_upload(filename),
            content_length,
        )
        resp = self._http.put(fileset_url, binary_stream, headers)

        if resp.status_code in [202, 204]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, fileset_url, [400, 401, 403, 404, 405, 412, 413]
            )

    def delete_fileset(
        self, status_or_fileset_url: typing.Union[StatusDocument, str]
    ) -> SWORDResponse:

        fileset_url = self._get_url(status_or_fileset_url, "fileset_url")
        resp = self._http.delete(fileset_url)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, fileset_url, [400, 401, 403, 404, 405, 412]
            )

    ###########################################################
    ## Utility methods
    ###########################################################

    def _get_url(self, source, url_property: str):
        if isinstance(source, str):
            return source
        return getattr(source, url_property)

    def _make_digest_header(self, digest: typing.Dict[str, str]):
        digest_parts = []
        for k, v in digest.items():
            digest_parts.append("{x}={y}".format(x=k, y=v))
        return ", ".join(digest_parts)

    def _raise_for_status_code(
        self, resp, request_url, expected=None, raise_generic_if_unexpected=True
    ):
        if expected is None:
            expected = [400, 401, 403, 404, 405, 412, 413, 415]

        if resp.status_code == 400 and 400 in expected:
            raise exceptions.SWORD3BadRequest(
                request_url, resp, "The server did not understand the request"
            )
        elif (resp.status_code == 401 and 401 in expected) or (
            resp.status_code == 403 and 403 in expected
        ):
            raise exceptions.SWORD3AuthenticationError(
                request_url, resp, "Authentication or authorisation failed"
            )
        elif resp.status_code == 404 and 404 in expected:
            raise exceptions.SWORD3NotFound(
                request_url, resp, "No resource found at requested URL"
            )
        elif resp.status_code == 405 and 405 in expected:
            raise exceptions.SWORD3OperationNotAllowed(
                request_url, resp, "The resource does not support this operation"
            )
        elif resp.status_code == 410 and 410 in expected:
            raise exceptions.SWORD3NotFound(
                request_url, resp, "The resource at requested URL has Gone"
            )
        elif resp.status_code == 412 and 412 in expected:
            raise exceptions.SWORD3PreconditionFailed(
                request_url,
                resp,
                "Your request could not be processed as-is, there may be inconsistencies in your request parameters",
            )
        elif resp.status_code == 413 and 413 in expected:
            raise exceptions.SWORD3MaxSizeExceeded(
                request_url,
                resp,
                "Your request exceeded the maximum deposit size for a single request against this server",
            )
        elif resp.status_code == 415 and 415 in expected:
            raise exceptions.SWORD3UnsupportedMediaType(
                request_url,
                resp,
                "The Content-Type that you sent was not supported by the server",
            )
        elif raise_generic_if_unexpected:
            raise exceptions.SWORD3WireError(
                request_url,
                resp,
                "Unexpected status code; unable to carry out protocol operation",
            )
