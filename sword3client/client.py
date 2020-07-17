from sword3client.connection import HttpLayer
from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client import SWORDResponse

from sword3common import (
    ServiceDocument,
    Metadata,
    StatusDocument,
    ContentDisposition,
    ByReference,
    MetadataAndByReference,
    SegmentedFileUpload,
    Error,
    constants,
)
from sword3common import exceptions

import json
import hashlib
import base64
import typing
import contextlib


class SWORD3Client(object):
    """The SWORDv3 client"""
    def __init__(self, http: HttpLayer=None):
        self._http = http if http is not None else RequestsHttpLayer()

    def set_http_layer(self, http):
        self._http = http

    def get_service(self, service_url: str) -> ServiceDocument:
        """Retrieves the SWORD service document for a given URL.

        :raises: SwordException"""
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
                resp, service_url, [400, 401, 403, 404, 405, 412, 413, 415],
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
            except exceptions.SeamlessException as e:
                raise exceptions.InvalidDataFromServer(
                    "Metadata retrieval got invalid metadata document: {x}".format(x=e.message),
                    response=resp
                ) from e
        else:
            self._raise_for_status_code(
                resp, metadata_url, [400, 401, 403, 404, 405, 412], request_context=constants.RequestContexts.Metadata
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
            "Content-Length": str(content_length),
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

    def append_by_reference(self,
        status_or_object_url: typing.Union[ServiceDocument, str],
        by_reference: ByReference,
        digest: typing.Dict[str, str] = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        object_url = self._get_url(status_or_object_url, "object_url")
        body_bytes, headers = self._by_reference_deposit_properties(
            by_reference, digest, in_progress=in_progress
        )
        resp = self._http.post(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 412, 413, 415]
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
    ## MD+BR methods
    #####################################################

    def create_object_with_metadata_and_by_reference(
            self,
            service: typing.Union[ServiceDocument, str],
            metadata_and_by_reference: MetadataAndByReference,
            digest: typing.Dict[str, str] = None,
            metadata_format: str = None,
            in_progress: bool = False,
    ) -> SWORDResponse:
        # get the service url.  The first argument may be the URL or the ServiceDocument
        service_url = self._get_url(service, "service_url")
        body_bytes, headers = self._mdbr_deposit_properties(
            metadata_and_by_reference, digest, metadata_format, in_progress
        )
        resp = self._http.post(service_url, body_bytes, headers)

        if resp.status_code in [201, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, service_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def append_metadata_and_by_reference(self,
            status_or_object_url: typing.Union[ServiceDocument, str],
            metadata_and_by_reference: MetadataAndByReference,
            digest: typing.Dict[str, str] = None,
            metadata_format: str = None,
            in_progress: bool = False,
    ) -> SWORDResponse:
        object_url = self._get_url(status_or_object_url, "object_url")
        body_bytes, headers = self._mdbr_deposit_properties(
            metadata_and_by_reference, digest,  metadata_format, in_progress=in_progress,
        )
        resp = self._http.post(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 412, 413, 415]
            )

    def _mdbr_deposit_properties(self,
                                 metadata_and_by_reference:MetadataAndByReference,
                                 digest: typing.Dict[str, str] = None,
                                 metadata_format: str = None,
                                 in_progress: bool = False,
                                 ):
        body = json.dumps(metadata_and_by_reference.data)
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
            "Content-Disposition": ContentDisposition.metadata_and_by_reference_upload().serialise(),
            "Digest": digest_val,
            "Metadata-Format" : metadata_format
        }

        if in_progress is not None:
            headers["In-Progress"] = "true" if in_progress else "false"

        return body_bytes, headers

    #####################################################
    ## Segmented file deposit operations
    #####################################################

    def create_object_with_temporary_file(
        self,
        service: typing.Union[ServiceDocument, str],
        temporary_url: str,
        filename: str,
        content_type: str,
        content_length: int = None,
        packaging: str = None,
        digest: typing.Dict[str, str] = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        br = ByReference()
        br.add_file(temporary_url,
                    filename,
                    content_type,
                    True,
                    content_length=content_length,
                    packaging=packaging,
                    digest=digest
                    )
        return self.create_object_by_reference(service, br, in_progress=in_progress)

    def append_temporary_file(
        self,
        status_or_object_url: typing.Union[ServiceDocument, str],
        temporary_url: str,
        filename: str,
        content_type: str,
        content_length: int = None,
        packaging: str = None,
        digest: typing.Dict[str, str] = None,
        in_progress: bool = False,
    ) -> SWORDResponse:

        br = ByReference()
        br.add_file(temporary_url,
                    filename,
                    content_type,
                    True,
                    content_length=content_length,
                    packaging=packaging,
                    digest=digest
                    )
        return self.append_by_reference(status_or_object_url, br, in_progress=in_progress)

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
            except exceptions.SeamlessException as e:
                raise exceptions.InvalidDataFromServer(
                    "Object retrieval got invalid status document: {x}".format(x=e.message),
                    response=resp,
                    request_url=object_url
                ) from e
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

    def replace_object_by_reference(self,
        status_or_object_url: typing.Union[StatusDocument, str],
        by_reference: ByReference,
        digest: typing.Dict[str, str] = None,
        in_progress: bool = False,
    ) -> SWORDResponse:
        object_url = self._get_url(status_or_object_url, "object_url")
        body_bytes, headers = self._by_reference_deposit_properties(
            by_reference,
            digest,
            in_progress=in_progress
        )
        resp = self._http.put(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 412, 413, 415]
            )

    def replace_object_with_metadata_and_by_reference(
            self,
            status_or_object_url: typing.Union[StatusDocument, str],
            metadata_and_by_reference: MetadataAndByReference,
            digest: typing.Dict[str, str] = None,
            metadata_format: str = None,
            in_progress: bool = False,
    ) -> SWORDResponse:
        object_url = self._get_url(status_or_object_url, "object_url")
        body_bytes, headers = self._mdbr_deposit_properties(
            metadata_and_by_reference, digest, metadata_format, in_progress=in_progress
        )
        resp = self._http.put(object_url, body_bytes, headers)

        if resp.status_code in [200, 202]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, object_url, [400, 401, 403, 404, 405, 412, 413, 415]
            )

    def replace_object_with_temporary_file(self,
            status_or_object_url: typing.Union[StatusDocument, str],
            temporary_url: str,
            filename: str,
            content_type: str,
            content_length: int = None,
            packaging: str = None,
            digest: typing.Dict[str, str] = None,
            in_progress: bool = False,
    ) -> SWORDResponse:
        br = ByReference()
        br.add_file(temporary_url,
                    filename,
                    content_type,
                    True,
                    content_length=content_length,
                    packaging=packaging,
                    digest=digest
                    )
        return self.replace_object_by_reference(status_or_object_url, br, in_progress=in_progress)

    #################################################
    ## Individual file protocol operations
    #################################################

    def get_file(self, file_url: str):
        @contextlib.contextmanager
        def file_getter():
            resp = self._http.get(file_url, stream=True)
            resp.__enter__()

            if resp.status_code >= 400:
                self._raise_for_status_code(
                    resp, file_url, [400, 401, 403, 404, 405, 412]
                )
            if resp.status_code != 200:
                raise exceptions.UnexpectedSwordException(
                    "Unexpected status code; unable to retrieve file",
                    response=resp,
                    request_url=file_url,
                    status_code=resp.status_code
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

    def replace_file_by_reference(
            self,
            file_url: str,
            by_reference: ByReference,
            digest: typing.Dict[str, str] = None
    ):
        body_bytes, headers = self._by_reference_deposit_properties(
            by_reference,
            digest
        )

        resp = self._http.put(file_url, body_bytes, headers)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, file_url, [400, 401, 403, 404, 405, 412, 413]
            )

    def replace_file_with_temporary_file(
            self,
            file_url: str,
            temporary_url: str,
            filename: str,
            content_type: str,
            content_length: int = None,
            digest: typing.Dict[str, str] = None
    ) -> SWORDResponse:

        br = ByReference()
        br.add_file(temporary_url,
                    filename,
                    content_type,
                    True,
                    content_length=content_length,
                    digest=digest
                    )
        return self.replace_file_by_reference(file_url, br)

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

    def replace_fileset_by_reference(self,
        status_or_fileset_url: typing.Union[StatusDocument, str],
        by_reference: ByReference,
        digest: typing.Dict[str, str] = None
    ) -> SWORDResponse:
        fileset_url = self._get_url(status_or_fileset_url, "fileset_url")
        body_bytes, headers = self._by_reference_deposit_properties(
            by_reference,
            digest,
        )
        resp = self._http.put(fileset_url, body_bytes, headers)

        if resp.status_code in [202, 204]:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, fileset_url, [400, 401, 403, 404, 405, 412, 413]
            )

    def replace_fileset_with_temporary_file(self,
            status_or_fileset_url: typing.Union[StatusDocument, str],
            temporary_url: str,
            filename: str,
            content_type: str,
            content_length: int = None,
            digest: typing.Dict[str, str] = None
    ) -> SWORDResponse:
        br = ByReference()
        br.add_file(temporary_url,
                    filename,
                    content_type,
                    True,
                    content_length=content_length,
                    digest=digest
                    )
        return self.replace_fileset_by_reference(status_or_fileset_url, br)

    ###########################################################
    ## Segmented upload operations
    ###########################################################

    def initialise_segmented_upload(self,
                                    service: typing.Union[ServiceDocument, str],
                                    assembled_size: int,
                                    segment_count: int,
                                    segment_size: int,
                                    digest: typing.Dict[str, str] = None
                                    ) -> SWORDResponse:
        staging_url = self._get_url(service, "staging_url")

        digest_val = None
        if digest is not None:
            digest_val = self._make_digest_header(digest)

        disp = ContentDisposition.initialise_segmented_upload(
            assembled_size,
            digest_val,
            segment_count,
            segment_size
        )

        headers = {
            "Content-Length" : 0,
            "Content-Disposition" : disp.serialise()
        }

        resp = self._http.post(staging_url, None, headers)

        if resp.status_code == 201:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, staging_url, [400, 401, 403, 404, 412, 413]
            )

    def upload_file_segment(self,
                            temporary_url: str,
                            binary_stream: typing.IO,
                            segment_number: int,
                            digest: typing.Dict[str, str] = None,
                            content_length: int = None
                            ) -> SWORDResponse:

        disp = ContentDisposition.upload_file_segment(segment_number)

        headers = {
            "Content-Disposition" : disp.serialise(),
            "Content-Type": "application/octet-stream"
        }

        if digest is not None:
            digest_val = self._make_digest_header(digest)
            headers["Digest"] = digest_val

        if content_length is not None:
            headers["Content-Length"] = content_length

        resp = self._http.post(temporary_url, binary_stream, headers)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, temporary_url, [400, 401, 403, 404, 405, 412]
            )

    def abort_segmented_upload(self, temporary_url: str) -> SWORDResponse:
        resp = self._http.delete(temporary_url)

        if resp.status_code == 204:
            return SWORDResponse(resp)
        else:
            self._raise_for_status_code(
                resp, temporary_url, [400, 401, 403, 404]
            )

    def segmented_upload_status(self,
                                     temporary_url: str
                                     ) -> SegmentedFileUpload:
        resp = self._http.get(temporary_url)

        if resp.status_code == 200:
            data = json.loads(resp.body)
            try:
                return SegmentedFileUpload(data)
            except exceptions.SeamlessException as e:
                raise exceptions.InvalidDataFromServer(
                    "Segmented File Upload retrieval got invalid information document: {x}".format(x=e.message),
                    response=resp
                ) from e
        else:
            self._raise_for_status_code(
                resp, temporary_url, [400, 401, 403, 404]
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
        self, resp, request_url, expected=None, request_context=None
    ):
        # set a default set of expected codes, if none is provided
        if expected is None:
            expected = [400, 401, 403, 404, 405, 412, 413, 415]

        # attempt to load an error doc out of the request body
        error_doc = None
        if resp.body is not None and resp.body != "":
            data = None
            try:
                data = json.loads(resp.body)
            except:
                # body isn't JSON
                # this will be dealt with below
                pass

            if data is not None:
                try:
                    error_doc = Error(data)
                except exceptions.SeamlessException as e:
                    # not valid data
                    # this will also be handled below
                    pass

        # first step in choosing what to raise is whether the status was expected
        if resp.status_code not in expected:
            name = error_doc.type if error_doc is not None else str(resp.status_code)
            raise exceptions.UnexpectedSwordException(
                "Received error code was not expected for this protocol operation",
                response=resp,
                error_doc=error_doc,
                status_code=resp.status_code,
                name=name
            )

        # next, if we were unable to extract an error document, see if we can raise just based on
        # the status code
        if error_doc is None or error_doc.type is None:
            possibles = exceptions.SwordException.for_status_code(resp.status_code)
            # if we only have one possible exception, raise it
            if len(possibles) == 1:
                raise possibles[0](possibles[0].reason, response=resp, request_url=request_url)

            # if we've been given a request context, filter the exceptions by the ones relevant to that context
            if request_context is not None:
                possibles = [p for p in possibles if len(p.contexts) == 0 or request_context in p.contexts]

            # if we're now down to one exception, raise it
            if len(possibles) == 1:
                raise possibles[0](possibles[0].reason, response=resp, request_url=request_url)

            # if we haven't raised an exception in this case so far, then raise an Ambiguous error
            raise exceptions.AmbiguousSwordException(
                "Error received from server could have been due to a number of things, and the server did not include details",
                response=resp,
                error_doc=error_doc,
                request_url=request_url,
                status_code=resp.status_code
            )

        raisable = exceptions.SwordException.for_type(error_doc.type)
        raise raisable(raisable.reason,
                       response=resp,
                       error_doc=error_doc,
                       request_url=request_url
        )

    #################################################
    ## Experiment, ingore for now
    #################################################

    """
    # Could put this in sword common
    CODES = {
        ("put", "object_url") : {"success" : [200, 202], "error" : [400, 401, 403]}
    }

    def _sword(self, url_or_obj, url_type, method, payload, request_generator, response_wrapper, request_context):
        url = self._get_url(url_or_obj, url_type)

        body_bytes_or_stream, headers = request_generator(payload)
        resp = getattr(self._http, method)(url, body_bytes_or_stream, headers)

        codes = SWORD3Client.CODES.get((method, url_type))
        if resp.status_code in codes["success"]:
            return response_wrapper(resp)
        else:
            self._raise_for_status_code(resp, url, expected=codes["error"], request_context=request_context)
    """