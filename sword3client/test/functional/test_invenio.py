from unittest import TestCase

from sword3client import SWORD3Client
from sword3client.connection.connection_requests import RequestsHttpLayer
from sword3client.test.mocks.connection import HttpMockFactory
from sword3client.lib import paths


from sword3common import constants, Metadata, ByReference, MetadataAndByReference, exceptions

from io import BytesIO
import hashlib
import base64
import os
import shutil
import math

SERVICE_URL = "http://localhost:8000/service-document"
DEPOSIT_URL = "http://localhost:8000/api/deposit"

AUTH_TOKEN = ""
INVENIO_HTTP_LAYER = RequestsHttpLayer(
    headers={"Authorization": "Bearer " + AUTH_TOKEN}
)
MOCK_MODE = True


class HttpLayerFactory(object):
    def __init__(self, default, use_mock):
        self._default = default
        self._use_mock = use_mock

    def __getattr__(self, item):
        if hasattr(self.__class__, item):
            return object.__getattribute__(self, item)

        if not self._use_mock:
            return self.get_default

        return getattr(HttpMockFactory, item)

    def get_default(self, *args, **kwargs):
        return self._default


HTTP_FACTORY = HttpLayerFactory(INVENIO_HTTP_LAYER, MOCK_MODE)


class TestInvenio(TestCase):
    def setUp(self) -> None:
        self.tmpFiles = []

    def tearDown(self) -> None:
        for tmpFile in self.tmpFiles:
            path = paths.rel2abs(__file__, "..", "tmp", tmpFile)
            if os.path.exists(path):
                os.remove(path)

    def test_01_service_document(self):
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)
        sd.verify_against_struct()

    def test_02_create_and_retrieve_with_metadata(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata)

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Retrieve the object itself
        client.set_http_layer(HTTP_FACTORY.get_object())
        status2 = client.get_object(status)
        status2.verify_against_struct()
        assert status.data == status2.data
        assert status.metadata_url is not None

        # 3. Retrieve the metadata back
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata))
        metadata2 = client.get_metadata(status2)
        metadata2.verify_against_struct()
        assert metadata.get_dc_field("creator") == metadata2.get_dc_field("creator")
        assert metadata.get_dcterms_field("rights") == metadata2.get_dcterms_field(
            "rights"
        )
        assert metadata.get_field("custom") == metadata2.get_field("custom")

    def test_03_create_object_with_binary(self):
        # 1. Create the object with a binary stream
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.create_object_with_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr = client.create_object_with_binary(
            SERVICE_URL,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
        )

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Download the file
        links = status.links
        assert len(links) == 1
        link = links[0]

        assert "@id" in link
        assert constants.REL_ORIGINAL_DEPOSIT in link.get("rel")
        assert link.get("contentType") == "text/plain"

        url = link.get("@id")
        client.set_http_layer(HTTP_FACTORY.get_file(BytesIO(bytes)))
        with client.get_file(url) as download:
            received = download.read()
        assert received == bytes

    def test_04_create_object_with_package(self):
        # 1. Create the object with a package
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        client = SWORD3Client(
            HTTP_FACTORY.create_object_with_package(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.zip",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "application/zip",
                        "packaging": constants.PACKAGE_SWORDBAGIT,
                    },
                ]
            )
        )

        with open(bag, "rb") as stream:
            dr = client.create_object_with_package(
                SERVICE_URL,
                stream,
                "test.zip",
                digest,
                content_type="application/zip",
                content_length=file_size,
                packaging=constants.PACKAGE_SWORDBAGIT,
            )

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Download the zip
        assert len(status.links) >= 1
        ods = status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])
        assert len(ods) == 1
        link = ods[0]

        assert "@id" in link
        assert "http://purl.org/net/sword/3.0/terms/originalDeposit" in link.get("rel")
        assert link.get("contentType") == "application/zip"

        filename = "test_invenio.test_04_create_object_with_package.zip"
        self.tmpFiles.append(filename)

        url = link.get("@id")
        data_out = paths.rel2abs(__file__, "..", "tmp", filename)
        with open(bag, "rb") as stream:
            client.set_http_layer(HTTP_FACTORY.get_file(stream))
            with client.get_file(url) as download:
                with open(data_out, "wb") as g:
                    shutil.copyfileobj(download, g)

        d2 = paths.sha256(data_out)
        assert d.hexdigest() == d2.hexdigest()

    def test_05_append_metadata_binary_package(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)

        url = dr.location

        # 2. Append some metadata
        metadata2 = Metadata()
        metadata2.add_dc_field("abstract", "This is an abstract")

        client.set_http_layer(HTTP_FACTORY.append_metadata())
        dr2 = client.append_metadata(url, metadata2, in_progress=True)

        assert dr2.status_code == 200
        assert dr2.location is not None

        status = dr2.status_document
        assert status is not None
        status.verify_against_struct()

        # 3. Check that metadata is appended correctly
        metadata.add_dc_field("abstract", "This is an abstract")
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata))
        metadata3 = client.get_metadata(status)

        assert metadata.get_dc_field("creator") == metadata3.get_dc_field("creator")
        assert metadata.get_dcterms_field("rights") == metadata3.get_dcterms_field(
            "rights"
        )
        assert metadata.get_field("custom") == metadata3.get_field("custom")
        assert metadata.get_field("abstract") == metadata3.get_field("abstract")

        # 4. add a binary file
        bytes = b"this is another random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.Rel.OriginalDeposit, constants.Rel.FileSetFile],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )
        dr3 = client.add_binary(
            status,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        assert dr3.status_code == 200
        assert dr3.location is not None
        status = dr3.status_document
        assert status is not None
        status.verify_against_struct()

        # 5. Retrieve the file again
        file_url = dr3.status_document.list_links(
            ["http://purl.org/net/sword/3.0/terms/fileSetFile"]
        )[0]["@id"]
        client.set_http_layer(HTTP_FACTORY.get_file(BytesIO(bytes)))
        with client.get_file(file_url) as download:
            received = download.read()
        assert received == bytes

        # 6. Append a package
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        client = SWORD3Client(
            HTTP_FACTORY.add_package(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.zip",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "application/zip",
                        "packaging": constants.PACKAGE_SWORDBAGIT,
                    },
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": constants.PACKAGE_BINARY,
                    },
                ]
            )
        )

        with open(bag, "rb") as stream:
            dr = client.add_package(
                status,
                stream,
                "test.zip",
                digest,
                content_type="application/zip",
                content_length=file_size,
                packaging=constants.PACKAGE_SWORDBAGIT,
            )

        assert dr.status_code == 200
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        assert len(status.links) >= 2
        ods = status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])
        assert len(ods) == 2

        # we don't bother retrieving the file, we've done plenty of that in other bits of the test

    def test_06_replace_metadata_binary(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)
        status = dr.status_document

        # 2. Add a binary file to it
        bytes = b"this is another random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client.set_http_layer(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.Rel.OriginalDeposit, constants.Rel.FileSetFile],
                        "contentType": "text/plain",
                        "packaging": constants.PACKAGE_BINARY,
                    }
                ]
            )
        )
        dr2 = client.add_binary(
            status,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        # 3. Replace the metadata
        metadata2 = Metadata()
        metadata2.add_dc_field("title", "My replacement")

        client.set_http_layer(HTTP_FACTORY.replace_metadata())
        dr3 = client.replace_metadata(status, metadata2)

        assert dr3.status_code == 204
        assert dr3.location is None
        assert dr3.status_document is None

        # 4. Retrieve the metadata to check it was replaced
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata2))
        metadata3 = client.get_metadata(status)

        assert metadata3.get_dc_field("creator") is None
        assert metadata3.get_dcterms_field("rights") is None
        assert metadata3.get_field("custom") is None
        assert metadata2.get_dc_field("title") == metadata3.get_dc_field("title")

        # 5. Replace the binary file
        bytes2 = b"this is a replacement stream of bytes"
        content_length2 = len(bytes2)
        d2 = hashlib.sha256(bytes2)
        digest2 = {constants.DIGEST_SHA_256: d2.digest()}
        stream2 = BytesIO(bytes2)

        client.set_http_layer(HTTP_FACTORY.replace_file())
        file_url = dr2.status_document.list_links(
            rels=["http://purl.org/net/sword/3.0/terms/fileSetFile"]
        )[0]["@id"]
        dr4 = client.replace_file(
            file_url, stream2, "text/plain", digest2, "test.bin", content_length2
        )

        # 6. Retrieve the file again
        client.set_http_layer(HTTP_FACTORY.get_file(BytesIO(bytes2)))
        with client.get_file(file_url) as download:
            received = download.read()
        assert received == bytes2

    def test_07_replace_fileset_with_binary(self):
        # 1. Create the object with a binary stream
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.create_object_with_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr = client.create_object_with_binary(
            SERVICE_URL,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        # 2. add another binary file
        bytes2 = b"this is another random stream of bytes"
        content_length2 = len(bytes2)
        d2 = hashlib.sha256(bytes2)
        digest2 = {constants.DIGEST_SHA_256: d2.digest()}
        stream2 = BytesIO(bytes2)

        client.set_http_layer(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                    {
                        "@id": "http://example.com/object/10/test2.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr2 = client.add_binary(
            dr.location,
            stream2,
            "test2.bin",
            digest2,
            content_length2,
            content_type="text/plain",
            in_progress=True,
        )

        # check that we have 2 files
        status = client.get_object(dr.location)
        assert len(status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])) == 2

        # 3. replace the fileset with a new binary
        bytes3 = b"this is a replacement stream of bytes"
        content_length3 = len(bytes3)
        d3 = hashlib.sha256(bytes3)
        digest3 = {constants.DIGEST_SHA_256: d3.digest()}
        stream3 = BytesIO(bytes3)

        client.set_http_layer(HTTP_FACTORY.replace_fileset_with_binary())
        dr3 = client.replace_fileset_with_binary(
            status.fileset_url,
            stream3,
            "test3.bin",
            digest3,
            content_length3,
            content_type="text/plain",
        )

        assert dr3.status_code == 204

        client.set_http_layer(
            HTTP_FACTORY.get_object(
                links=[
                    {
                        "@id": "http://example.com/object/10/test3.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )

        status = client.get_object(status)
        assert len(status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])) == 1

    def test_08_replace_object_metadata_binary_package(self):
        # 1. Create an object with some metadata
        metadata = Metadata()
        metadata.add_dc_field("title", "Replace Test")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)
        status = dr.status_document

        # 2. Replace the object with a binary file
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client.set_http_layer(HTTP_FACTORY.replace_object_with_binary())
        dr2 = client.replace_object_with_binary(
            status,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        # 3. Check the object and the metadata
        client.set_http_layer(
            HTTP_FACTORY.get_object(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )

        status = client.get_object(status)
        assert len(status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])) == 1

        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata=Metadata()))
        metadata = client.get_metadata(status)
        assert metadata.get_dc_field("title") is None

        # 4. Replace the object with metadata
        metadata2 = Metadata()
        metadata2.add_dc_field("title", "More metadata")

        client.set_http_layer(HTTP_FACTORY.replace_object_with_metadata(links=[]))
        dr3 = client.replace_object_with_metadata(status, metadata2, in_progress=True)

        # 5. check that the files are gone and the new metadata is in
        status = dr3.status_document
        assert len(status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])) == 0

        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata=metadata2))
        metadata3 = client.get_metadata(status)
        assert metadata3.get_dc_field("title") == metadata2.get_dc_field("title")

        # 6. replace the object with packaged content
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        client.set_http_layer(HTTP_FACTORY.replace_object_with_package())

        with open(bag, "rb") as stream:
            dr4 = client.replace_object_with_package(
                status,
                stream,
                "SWORDBagIt.zip",
                digest,
                content_type="application/zip",
                content_length=file_size,
                packaging=constants.PACKAGE_SWORDBAGIT,
            )

        # 7. Check the object and the metadata
        client.set_http_layer(
            HTTP_FACTORY.get_object(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.zip",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "application/zip",
                        "packaging": constants.PACKAGE_SWORDBAGIT,
                    }
                ]
            )
        )

        status = client.get_object(status)
        assert len(status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])) == 1

        resp_md = Metadata()
        resp_md.add_dc_field("title", "The title")
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata=resp_md))
        metadata = client.get_metadata(status)
        assert metadata.get_dc_field("title") == "The title"

    def test_09_delete(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("title", "Test delete")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)

        status = dr.status_document

        # 2. Add 2 binary files
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client.set_http_layer(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )
        dr2 = client.add_binary(
            status,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        bytes2 = b"this is another random stream of bytes"
        content_length2 = len(bytes2)
        d2 = hashlib.sha256(bytes2)
        digest2 = {constants.DIGEST_SHA_256: d2.digest()}
        stream2 = BytesIO(bytes2)

        client.set_http_layer(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                    {
                        "@id": "http://example.com/object/10/test2.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr3 = client.add_binary(
            status,
            stream2,
            "test2.bin",
            digest2,
            content_length2,
            content_type="text/plain",
            in_progress=True,
        )

        # 3. Delete the object metadata
        client.set_http_layer(HTTP_FACTORY.delete_metadata())
        dr4 = client.delete_metadata(status)

        assert dr4.status_code == 204

        # 4. Check that the metadata is gone
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata=Metadata()))
        metadata2 = client.get_metadata(status)
        assert metadata2.get_dc_field("title") is None

        # Refresh status document
        client.set_http_layer(
            HTTP_FACTORY.get_object(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                    {
                        "@id": "http://example.com/object/10/test2.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        status = client.get_object(status)

        # 5. Delete one of the files
        file_url = status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])[0].get(
            "@id"
        )
        client.set_http_layer(HTTP_FACTORY.delete_file())
        dr5 = client.delete_file(file_url)

        assert dr5.status_code == 204

        # 6. Retrieve the updated status and check the file is gone
        client.set_http_layer(
            HTTP_FACTORY.get_object(
                links=[
                    {
                        "@id": "http://example.com/object/10/test2.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )
        status = client.get_object(status)

        ods = status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])
        assert len(ods) == 1
        assert file_url not in [od.get("@id") for od in ods]

        # 7. Delete the fileset
        client.set_http_layer(HTTP_FACTORY.delete_fileset())
        dr6 = client.delete_fileset(status.fileset_url)

        assert dr6.status_code == 204

        # 8. Retrieve the updated status and check the files are all gone
        client.set_http_layer(HTTP_FACTORY.get_object(links=[]))
        status = client.get_object(status)

        ods = status.list_links(rels=[constants.REL_ORIGINAL_DEPOSIT])
        assert len(ods) == 0

        # 9. Delete the entire object
        client.set_http_layer(HTTP_FACTORY.delete_object())
        dr7 = client.delete_object(status)

        assert dr7.status_code in [200, 202, 204]

        # 10. Attempt to retrieve the object
        client.set_http_layer(HTTP_FACTORY.get_object(not_found=True))
        with self.assertRaises(exceptions.NotFound):
            client.get_object(status)

    def test_10_create_object_by_reference(self):
        HOSTED_FILE = "https://github.com/swordapp/sword3-client.py/raw/master/sword3client/test/resources/SWORDBagIt.zip"
        LINKS = [
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference.zip",
                "byReference": HOSTED_FILE,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            }
        ]

        # 1. Create an object by reference
        br = ByReference()
        br.add_file(HOSTED_FILE,
                    "test.bin",
                    "application/octet-stream",
                    True)

        client = SWORD3Client(HTTP_FACTORY.create_object_by_reference(links=LINKS))
        dr = client.create_object_by_reference(SERVICE_URL, br)

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Retrieve the object itself
        client.set_http_layer(HTTP_FACTORY.get_object(links=LINKS))
        status2 = client.get_object(status)
        status2.verify_against_struct()
        assert status.data == status2.data

        # 3. Look in the files to see if we can see the byReference file
        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == HOSTED_FILE

    def test_11_create_with_metadata_and_by_reference(self):
        HOSTED_FILE = "https://github.com/swordapp/sword3-client.py/raw/master/sword3client/test/resources/SWORDBagIt.zip"
        LINKS = [
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference.zip",
                "byReference": HOSTED_FILE,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            }
        ]

        # 1. Create an object by reference
        br = ByReference()
        br.add_file(HOSTED_FILE,
                    "test.bin",
                    "application/octet-stream",
                    True)

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        mdbr = MetadataAndByReference(metadata, br)

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata_and_by_reference(links=LINKS))
        dr = client.create_object_with_metadata_and_by_reference(SERVICE_URL, mdbr)

        assert dr.status_code == 201
        assert dr.location is not None

        status = dr.status_document
        assert status is not None
        status.verify_against_struct()

        # 2. Retrieve the object itself
        client.set_http_layer(HTTP_FACTORY.get_object(links=LINKS))
        status2 = client.get_object(status)
        status2.verify_against_struct()
        assert status.data == status2.data

        # 3. Look in the files to see if we can see the byReference file
        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == HOSTED_FILE

        # 4. Retrieve the metadata back
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata))
        metadata2 = client.get_metadata(status2)
        metadata2.verify_against_struct()
        assert metadata.get_dc_field("creator") == metadata2.get_dc_field("creator")
        assert metadata.get_dcterms_field("rights") == metadata2.get_dcterms_field("rights")
        assert metadata.get_field("custom") == metadata2.get_field("custom")

    def test_12_segmented_upload(self):
        # set up by preparing our binary file to upload
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        # 1. Obtain the service document, which is where we will find a reference to the staging endpoint
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)

        # 2. Initialise a segmented upload on the staging endpoint with the parameters derived from our test file
        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )

        temporary_url = resp.location
        assert temporary_url is not None

        # 3. Upload a couple of the file segments
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            segment1 = f.read(segment_size)
            stream1 = BytesIO(segment1)
            client.upload_file_segment(temporary_url, stream1, 1)

            segment2 = f.read(segment_size)
            stream2 = BytesIO(segment2)
            client.upload_file_segment(temporary_url, stream2, 2)

        # 4. Retrieve the segmented file upload information to see if it contains what we expect
        client.set_http_layer(HTTP_FACTORY.segmented_upload_status([1,2], [3,4,5], file_size, segment_size))
        sus = client.segmented_upload_status(temporary_url)

        assert sus.received == [1,2]
        assert sus.expecting == [3,4,5]
        assert sus.size == file_size
        assert sus.segment_size == segment_size

        # 5. Abort the upload
        client.set_http_layer(HTTP_FACTORY.abort_segmented_upload())
        resp = client.abort_segmented_upload(temporary_url)

        assert resp.status_code == 204

        # 6. Check that the upload has actually been aborted by attempting to retrieve again
        client.set_http_layer(HTTP_FACTORY.not_found())
        with self.assertRaises(exceptions.NotFound):
            client.segmented_upload_status(temporary_url)

    def test_13_temporary_file_deposit(self):
        # set up by preparing our binary file to upload
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        # 1. Obtain the service document, which is where we will find a reference to the staging endpoint
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)

        # 2. Initialise a segmented upload on the staging endpoint with the parameters derived from our test file
        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )
        temporary_url = resp.location

        # 3. Upload all of the file segments
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url, stream, i)

        # 4. Deposit the temporary file to the repository
        client.set_http_layer(HTTP_FACTORY.create_object_with_temporary_file(links=[
            {
                "@id" : "http://example.com/object/1/temp.zip",
                "rel" : [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit, constants.Rel.FileSetFile],
                "byReference" : temporary_url,
                "status" : constants.FileState.Pending
            }
        ]))
        resp = client.create_object_with_temporary_file(SERVICE_URL, temporary_url, "test.zip", "application/zip")

        assert resp.status_code == 201
        assert resp.location is not None

        status = resp.status_document

        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == temporary_url

    def test_14_append_by_reference_then_mdbr(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)

        url = dr.location

        # 2. Append a file by reference
        HOSTED_FILE = "https://github.com/swordapp/sword3-client.py/raw/master/sword3client/test/resources/SWORDBagIt.zip"
        LINKS = [
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference.zip",
                "byReference": HOSTED_FILE,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            }
        ]

        br = ByReference()
        br.add_file(HOSTED_FILE,
                    "test.bin",
                    "application/octet-stream",
                    True)

        client = SWORD3Client(HTTP_FACTORY.append_by_reference(links=LINKS))
        dr = client.append_by_reference(url, br)

        assert dr.status_code == 200

        # 3. Look in the files to see if we can see the byReference file
        status = dr.status_document
        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == HOSTED_FILE


        # 4. Now append again with both metadata and by-reference
        HOSTED_FILE_2 = "https://github.com/swordapp/sword3-client.py/raw/master/sword3client/test/resources/SWORDBagIt.zip#different"
        LINKS.append({
            "status": constants.FileState.Pending,
            "eTag": "1",
            "@id": "http://www.myorg.ac.uk/sword3/object1/reference2.zip",
            "byReference": HOSTED_FILE,
            "rel": [
                constants.Rel.ByReferenceDeposit,
                constants.Rel.OriginalDeposit,
                constants.Rel.FileSetFile
            ]
        })

        br2 = ByReference()
        br2.add_file(HOSTED_FILE_2,
                    "test2.bin",
                    "application/octet-stream",
                    True)

        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        mdbr = MetadataAndByReference(metadata, br2)

        client = SWORD3Client(HTTP_FACTORY.append_metadata_and_by_reference(links=LINKS))
        dr2 = client.append_metadata_and_by_reference(status, mdbr)

        # 5. Check the files to see that the new by reference has been attached
        status2 = dr2.status_document
        ods = status2.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 2
        for brl in ods:
            assert "byReference" in brl
            assert brl["byReference"] in [HOSTED_FILE, HOSTED_FILE_2]

        # 6. check out metadata was appended
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata))
        metadata2 = client.get_metadata(status)

        assert metadata.get_dc_field("creator") == metadata2.get_dc_field("creator")
        assert metadata.get_dcterms_field("rights") == metadata2.get_dcterms_field("rights")
        assert metadata.get_field("custom") == metadata2.get_field("custom")

    def test_15_append_temporary_file(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata)

        # set up by preparing our binary file to upload
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        # 2. Obtain the service document, which is where we will find a reference to the staging endpoint
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)

        # 3. Initialise a segmented upload on the staging endpoint with the parameters derived from our test file
        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )
        temporary_url = resp.location

        # 4. Upload all of the file segments
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url, stream, i)

        # 5. Deposit the temporary file to the repository
        client.set_http_layer(HTTP_FACTORY.append_temporary_file(links=[
            {
                "@id": "http://example.com/object/1/temp.zip",
                "rel": [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit, constants.Rel.FileSetFile],
                "byReference": temporary_url,
                "status": constants.FileState.Pending
            }
        ]))
        resp = client.append_temporary_file(dr.status_document, temporary_url, "test.zip", "application/octet-stream")

        assert resp.status_code == 200

        status = resp.status_document

        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == temporary_url

        # 6. Now send upload the file again, so we can send it as a package
        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )
        temporary_url = resp.location

        # 7. Upload all of the file segments (again)
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url, stream, i)

        # 8. Deposit the temporary file to the repository as a package
        client.set_http_layer(HTTP_FACTORY.append_temporary_file(links=[
            {
                "@id": "http://example.com/object/1/temp.zip",
                "rel": [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit, constants.Rel.FileSetFile],
                "byReference": temporary_url,
                "status": constants.FileState.Pending
            },
            {
                "@id": "http://example.com/object/1/temp2.zip",
                "rel": [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit, constants.Rel.FileSetFile],
                "byReference": temporary_url,
                "status": constants.FileState.Pending,
                "packaging" : constants.PACKAGE_SWORDBAGIT
            }
        ]))
        resp = client.append_temporary_file(dr.status_document, temporary_url, "test2.zip", "application/zip", packaging=constants.PACKAGE_SWORDBAGIT)

        assert resp.status_code == 200

        status = resp.status_document

        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 2
        trip_wire = False
        for brl in ods:
            if "packaging" in brl:
                assert brl["packaging"] == constants.PACKAGE_SWORDBAGIT
                trip_wire = True

        assert trip_wire

    def test_16_replace_files_with_by_reference(self):
        HOSTED_FILE = "https://github.com/swordapp/sword3-client.py/raw/master/sword3client/test/resources/SWORDBagIt.zip"

        # 1. Create the object with a binary stream
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.create_object_with_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr = client.create_object_with_binary(
            SERVICE_URL,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
        )

        # 2. Replace that file by reference
        status = dr.status_document
        links = status.list_links(rels=[constants.Rel.OriginalDeposit])
        file_url = links[0].get("@id")

        br = ByReference()
        br.add_file(HOSTED_FILE,
                    "test2.bin",
                    "application/octet-stream",
                    True)

        client.set_http_layer(HTTP_FACTORY.replace_file_by_reference())
        dr2 = client.replace_file_by_reference(file_url, br)

        # 3. Retrieve the object
        client.set_http_layer(HTTP_FACTORY.get_object(links=[{
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference.zip",
                "byReference": HOSTED_FILE,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
        }]))
        status2 = client.get_object(status)
        links = status2.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(links) == 1

        # 4. Now replace the enitre fileset with a couple of by reference files
        br2 = ByReference()
        br2.add_file(HOSTED_FILE,
                    "test3.bin",
                    "application/octet-stream",
                    True)
        br2.add_file(HOSTED_FILE + "#different",
                    "test4.bin",
                    "application/octet-stream",
                    True)

        client.set_http_layer(HTTP_FACTORY.replace_fileset_by_reference())
        dr3 = client.replace_fileset_by_reference(status2, br2)

        assert dr3.status_code == 204

        # 5. Retrieve the object again
        client.set_http_layer(HTTP_FACTORY.get_object(links=[
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference2.zip",
                "byReference": HOSTED_FILE,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            },
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference3.zip",
                "byReference": HOSTED_FILE + "#different",
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            }
        ]))
        status3 = client.get_object(status)
        links = status3.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(links) == 2

    def test_17_replace_file_with_temporary_file(self):
        # set up by preparing our binary file to upload
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        # 1. Create the object with a binary stream
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.create_object_with_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr = client.create_object_with_binary(
            SERVICE_URL,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
        )

        # 2. Obtain the service document, which is where we will find a reference to the staging endpoint
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)

        # 3. Initialise a segmented upload on the staging endpoint with the parameters derived from our test file
        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )
        temporary_url = resp.location

        # 4. Upload all of the file segments
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url, stream, i)

        # 5. Replace the current file with the new file
        status = dr.status_document
        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        file_url = ods[0].get("@id")

        client.set_http_layer(HTTP_FACTORY.replace_file_with_temporary_file())
        resp = client.replace_file_with_temporary_file(file_url, temporary_url, "test2.zip", "application/octet-stream")
        assert resp.status_code == 204

        # 6. Retrieve the updated status document
        client.set_http_layer(HTTP_FACTORY.get_object(links=[
            {
                "@id": "http://example.com/object/1/temp.zip",
                "rel": [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit, constants.Rel.FileSetFile],
                "byReference": temporary_url,
                "status": constants.FileState.Pending
            }
        ]))
        status2 = client.get_object(status)

        # 7. Check the status document for the replacement file
        ods = status2.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == temporary_url

    def test_18_replace_fileset_with_temporary_file(self):
        # set up by preparing our binary file to upload
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        bag_digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)


        # 1. Create the object with a binary stream
        bytes = b"this is a random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.create_object_with_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.REL_ORIGINAL_DEPOSIT],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                ]
            )
        )
        dr = client.create_object_with_binary(
            SERVICE_URL,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
        )

        # 2. add a second binary stream, so there are a couple of files in the fileset
        bytes = b"this is another random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.Rel.OriginalDeposit, constants.Rel.FileSetFile],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    },
                    {
                        "@id": "http://example.com/object/10/test2.bin",
                        "rel": [constants.Rel.OriginalDeposit, constants.Rel.FileSetFile],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )
        dr2 = client.add_binary(
            dr.status_document,
            stream,
            "test2.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        status = dr2.status_document
        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 2

        # 3. Obtain the service document, which is where we will find a reference to the staging endpoint
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)

        # 4. Initialise a segmented upload on the staging endpoint with the parameters derived from our test file
        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=bag_digest
        )
        temporary_url = resp.location

        # 5. Upload all of the file segments
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url, stream, i)

        # 6. Replace the current fileset with the temporary file
        client.set_http_layer(HTTP_FACTORY.replace_fileset_with_temporary_file())
        resp = client.replace_fileset_with_temporary_file(status, temporary_url, "test3.zip",
                                                       "application/octet-stream")
        assert resp.status_code == 204

        # 6. Retrieve the updated status document
        client.set_http_layer(HTTP_FACTORY.get_object(links=[
            {
                "@id": "http://example.com/object/1/temp.zip",
                "rel": [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit,
                        constants.Rel.FileSetFile],
                "byReference": temporary_url,
                "status": constants.FileState.Pending
            }
        ]))
        status2 = client.get_object(status)

        # 7. Check the status document for the replacement file
        ods = status2.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == temporary_url

    def test_19_replace_object_by_reference_and_mdbr(self):
        HOSTED_FILE = "https://github.com/swordapp/sword3-client.py/raw/master/sword3client/test/resources/SWORDBagIt.zip"

        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata)

        # 2. add a binary file
        bytes = b"this is another random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.Rel.OriginalDeposit, constants.Rel.FileSetFile],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )
        dr2 = client.add_binary(
            dr.status_document,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        # 3. Replace the object by reference
        status = dr2.status_document

        br = ByReference()
        br.add_file(HOSTED_FILE,
                     "test3.bin",
                     "application/octet-stream",
                     True)
        br.add_file(HOSTED_FILE + "#different",
                     "test4.bin",
                     "application/octet-stream",
                     True)

        client.set_http_layer(HTTP_FACTORY.replace_object_by_reference(links=[
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference.zip",
                "byReference": HOSTED_FILE,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            },
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference2.zip",
                "byReference": HOSTED_FILE + "#different",
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            },
        ]))
        dr3 = client.replace_object_by_reference(status, br)

        # 4. Check the links that we expect
        status2 = dr3.status_document
        links = status2.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(links) == 2

        # 5. Acquire the metadata and check that it is empty
        client.set_http_layer(HTTP_FACTORY.get_metadata(Metadata()))
        metadata2 = client.get_metadata(status)

        assert metadata2.get_dc_field("creator") is None
        assert metadata2.get_dcterms_field("rights") is None
        assert metadata2.get_field("custom") is None

        # 6. Now replace the metadata and by reference files at the same time
        br = ByReference()
        br.add_file(HOSTED_FILE + "#moredifferent",
                    "test3.bin",
                    "application/octet-stream",
                    True)

        metadata3 = Metadata()
        metadata3.add_dc_field("title", "Replacement")

        mdbr = MetadataAndByReference(metadata3, br)

        client.set_http_layer(HTTP_FACTORY.replace_object_with_metadata_and_by_reference(links=[
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference3.zip",
                "byReference": HOSTED_FILE + "#moredifferent",
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            }
        ]))
        dr4 = client.replace_object_with_metadata_and_by_reference(dr3.status_document, mdbr)

        assert dr4.status_code == 200
        status3 = dr4.status_document
        links = status3.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(links) == 1

        # 7. Retrieve the metadata and check it was replaced
        client.set_http_layer(HTTP_FACTORY.get_metadata(metadata3))
        metadata2 = client.get_metadata(status)

        assert metadata2.get_dc_field("title") == "Replacement"

    def test_20_replace_object_with_temporary_file(self):
        # 1. Create an object with the metadata
        metadata = Metadata()
        metadata.add_dc_field("creator", "Test")
        metadata.add_dcterms_field("rights", "All of them")
        metadata.add_field("custom", "entry")

        client = SWORD3Client(HTTP_FACTORY.create_object_with_metadata())
        dr = client.create_object_with_metadata(SERVICE_URL, metadata)

        # 2. add a binary file
        bytes = b"this is another random stream of bytes"
        content_length = len(bytes)
        d = hashlib.sha256(bytes)
        digest = {constants.DIGEST_SHA_256: d.digest()}
        stream = BytesIO(bytes)

        client = SWORD3Client(
            HTTP_FACTORY.add_binary(
                links=[
                    {
                        "@id": "http://example.com/object/10/test.bin",
                        "rel": [constants.Rel.OriginalDeposit, constants.Rel.FileSetFile],
                        "contentType": "text/plain",
                        "packaging": "http://purl.org/net/sword/3.0/package/Binary",
                    }
                ]
            )
        )
        dr2 = client.add_binary(
            dr.status_document,
            stream,
            "test.bin",
            digest,
            content_length,
            content_type="text/plain",
            in_progress=True,
        )

        # 3. Obtain the service document, which is where we will find a reference to the staging endpoint
        client = SWORD3Client(HTTP_FACTORY.get_service())
        sd = client.get_service(SERVICE_URL)

        # 4. Initialise a segmented upload on the staging endpoint with the parameters derived from our test file
        # set up by preparing our binary file to upload
        bag = paths.rel2abs(__file__, "..", "resources", "SWORDBagIt.zip")
        d = paths.sha256(bag)
        digest = {constants.DIGEST_SHA_256: base64.b64encode(d.digest())}
        file_size = os.path.getsize(bag)

        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )
        temporary_url = resp.location

        # 5. Upload all of the file segments
        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url, stream, i)

        # 6. replace the object with the file
        client.set_http_layer(HTTP_FACTORY.replace_object_with_temporary_file(links=[
            {
                "status": constants.FileState.Pending,
                "eTag": "1",
                "@id": "http://www.myorg.ac.uk/sword3/object1/reference.zip",
                "byReference": temporary_url,
                "rel": [
                    constants.Rel.ByReferenceDeposit,
                    constants.Rel.OriginalDeposit,
                    constants.Rel.FileSetFile
                ]
            }
        ]))
        dr3 = client.replace_object_with_temporary_file(dr.status_document, temporary_url, "test2.zip", "application/octet-stream")

        assert dr3.status_code == 200
        status = dr3.status_document
        ods = status.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        brl = ods[0]
        assert "byReference" in brl
        assert brl["byReference"] == temporary_url

        # we won't bother checking the metadata, the previous test should prove that fine

        # 7. Set up another temporary file, to try a package deposit
        segment_count = 5
        segment_size = math.ceil(file_size / segment_count)

        client.set_http_layer(HTTP_FACTORY.initialise_segmented_upload())
        resp = client.initialise_segmented_upload(
            sd,
            assembled_size=file_size,
            segment_count=segment_count,
            segment_size=segment_size,
            digest=digest
        )
        temporary_url2 = resp.location

        client.set_http_layer(HTTP_FACTORY.upload_file_segment())
        with open(bag, "rb") as f:
            for i in range(segment_count):
                segment = f.read(segment_size)
                stream = BytesIO(segment)
                client.upload_file_segment(temporary_url2, stream, i)

        # 8. upload the file, asserting that it's a package
        client.set_http_layer(HTTP_FACTORY.replace_object_with_temporary_file(links=[
            {
                "@id": "http://example.com/object/1/temp2.zip",
                "rel": [constants.Rel.OriginalDeposit, constants.Rel.ByReferenceDeposit, constants.Rel.FileSetFile],
                "byReference": temporary_url2,
                "status": constants.FileState.Pending,
                "packaging" : constants.PACKAGE_SWORDBAGIT
            }
        ]))
        dr4 = client.replace_object_with_temporary_file(dr.status_document, temporary_url, "test2.zip",
                                                        "application/zip", packaging=constants.PACKAGE_SWORDBAGIT)

        assert dr4.status_code == 200
        status2 = dr4.status_document
        ods = status2.list_links(rels=[constants.Rel.OriginalDeposit])
        assert len(ods) == 1
        trip_wire = False
        for brl in ods:
            if "packaging" in brl:
                assert brl["packaging"] == constants.PACKAGE_SWORDBAGIT
                trip_wire = True

        assert trip_wire