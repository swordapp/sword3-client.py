Getting Started
===============

Installation
------------

You can install the SWORDv3 client from PyPI as `sword3client
<https://pypi.org/project/sword3client/>`_.

Making a client
---------------

Create a new instance of the client

.. code:: python

    from sword3client import SWORD3Client
    client = SWORD3Client()

See the object definitions for full details of all operations available.


Create an object with metadata only
-----------------------------------

.. code:: python

    from sword3common import Metadata
    from sword3client import SWORD3Client
    client = SWORD3Client()

    SERVICE = "http://example.com/service-document"
    metadata = Metadata()
    metadata.add_dc_field("creator", "Test")
    response = client.create_object_with_metadata(SERVICE, metadata)


Create an object with a package
-------------------------------

.. code:: python

    from sword3common import constants
    from sword3client import SWORD3Client
    client = SWORD3Client()

    package_path = "/path/to/file.zip"
    digest = {constants.DIGEST_SHA_256: "digest...."}
    SERVICE = "http://example.com/service-document"
    with open(package_path, "rb") as stream:
        response = client.create_object_with_package(
                    SERVICE,
                    stream,
                    "test.zip",
                    digest,
                    content_type="application/zip",
                    packaging=constants.PACKAGE_SWORDBAGIT,
                )


Retrieve the Object's status
----------------------------

.. code:: python

    from sword3client import SWORD3Client
    client = SWORD3Client()

    OBJ_URL = "http://example.com/object/1"
    status = client.get_object(OBJ_URL)


Append a binary file
--------------------

.. code:: python

    from sword3client import SWORD3Client
    client = SWORD3Client()

    OBJ_URL = "http://example.com/object/1"
    file_path = "/path/to/binary.bin"
    digest = {sword3common.constants.DIGEST_SHA_256: "digest...."}
    with open(file_path, "rb") as stream:
        response = client.add_binary(OBJ_URL, stream, "test.bin", digest)


Delete the object
-----------------

.. code:: python

    from sword3client import SWORD3Client
    client = SWORD3Client()

    OBJ_URL = "http://example.com/object/1"
    response = client.delete_object(OBJ_URL)


Create an object by reference
-----------------------------

.. code:: python

    from sword3common import ByReference
    from sword3client import SWORD3Client
    client = SWORD3Client()

    SERVICE = "http://example.com/service-document"

    br = ByReference()
    br.add_file("http://example.com/file.pdf",
            "file.pdf",
            "application/pdf",
            True)

    response = client.create_object_by_reference(SERVICE, br)

Upload a large file by segments
-------------------------------

.. code:: python

    from io import BytesIO
    from sword3common import constants
    from sword3client import SWORD3Client
    client = SWORD3Client()

    SERVICE = "http://example.com/service-document"
    FILE_SIZE = 1000000
    SEGMENT_COUNT = 10
    SEGMENT_SIZE = 100000
    DIGEST = {constants.DIGEST_SHA_256: "digest...."}
    LARGE_FILE = "/path/to/large/file.zip"

    # get the service document, which tells us important details on segmented uploads
    service_document = client.get_service(SERVICE)

    # initialise the upload, to get a temporary url
    resp = client.initialise_segmented_upload(
        service_document,
        assembled_size=FILE_SIZE,
        segment_count=SEGMENT_COUNT,
        segment_size=SEGMENT_SIZE,
        digest=DIGEST
    )
    temporary_url = resp.location

    # send each segment to the temporary url
    with open(LARGE_FILE, "rb") as f:
        for i in range(SEGMENT_COUNT):
            segment = f.read(SEGMENT_SIZE)
            stream = BytesIO(segment)
            segment_response = client.upload_file_segment(temporary_url, stream, i)

Retrieve information about a segmented upload
---------------------------------------------

.. code:: python

    from sword3client import SWORD3Client
    client = SWORD3Client()

    # Temporary URL obtained from initialisation of segmented upload step (see above)
    TEMPORARY_URL = "http://example.com/temporary_url"

    upload_status = client.segmented_upload_status(TEMPORARY_URL)

    print(upload_status.received)
    print(upload_status.expecting)
    print(upload_status.size)
    print(upload_status.segment_size)


Deposit a file uploaded by segments
-----------------------------------

.. code:: python

    from sword3client import SWORD3Client
    client = SWORD3Client()

    SERVICE = "http://example.com/service-document"

    # Temporary URL obtained from initialisation of segmented upload step (see above)
    TEMPORARY_URL = "http://example.com/temporary_url"

    resp = client.create_object_with_temporary_file(SERVICE,
                                                TEMPORARY_URL,
                                                "test.zip",
                                                "application/zip")


Creating an object with metadata and then add a file
----------------------------------------------------

Here's an example of usage, to create a deposit with metadata and a single file:

.. code:: python

    from sword3client import SWORD3Client
    from sword3common import Metadata

    metadata = Metadata()
    metadata.add_dc_field("creator", "Smith, J.")
    metadata.add_dcterms_field("license", "https://creativecommons.org/licenses/by-sa/4.0/")
    metadata.add_field("custom", "entry")

    client = SWORD3Client()

    # create the object with the metadata document, and set in_progress=True to allow
    # us to come back and add more content to the object
    dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)

    with open('data-table.csv') as f:
        # calcuate the SHA-256 for the binary
        sha256 = hashlib.sha256()
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

        content_length = f.tell()
        f.seek(0)

        digest = {constants.DIGEST_SHA_256: sha256.digest()}

        # send the binary file to be added to the object
        client.add_binary(
            dr.status_document,
            f,
            'data-table.csv',
            digest,
            content_length,
            content_type="text/csv"
        )

