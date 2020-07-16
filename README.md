# SWORDv3 Client

[![Documentation Status](https://readthedocs.org/projects/sword3-clientpy/badge/?version=latest)](https://sword3-clientpy.readthedocs.io/en/latest/?badge=latest)

This client library provides all the basic features of SWORDv3 as a Python API.

## Example Usage

Create a new instance of the client

```python
from sword3client import SWORD3Client
client = SWORD3Client()
```

See the object definitions for full details of all operations available.  Examples of common usage would be:

* Create an object with metadata only:

```python
from sword3common import Metadata
from sword3client import SWORD3Client
client = SWORD3Client()

SERVICE = "http://example.com/service-document"
metadata = Metadata()
metadata.add_dc_field("creator", "Test")
response = client.create_object_with_metadata(SERVICE, metadata)
```

* Create an object with a package:

```python
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
```

* Retrieve the Object's status:

```python
from sword3client import SWORD3Client
client = SWORD3Client()

OBJ_URL = "http://example.com/object/1"
status = client.get_object(OBJ_URL)
```

* Append a binary file:

```python
from sword3client import SWORD3Client
client = SWORD3Client()

OBJ_URL = "http://example.com/object/1"
file_path = "/path/to/binary.bin"
digest = {sword3common.constants.DIGEST_SHA_256: "digest...."}
with open(file_path, "rb") as stream:
    response = client.add_binary(OBJ_URL, stream, "test.bin", digest)
```

* Delete the object:

```python
from sword3client import SWORD3Client
client = SWORD3Client()

OBJ_URL = "http://example.com/object/1"
response = client.delete_object(OBJ_URL)
```

* Create an object by reference:

```python
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
```

* Upload a large file by segments

```python
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
```

* Retrieve information about a segmented upload

```python
from sword3client import SWORD3Client
client = SWORD3Client()

# Temporary URL obtained from initialisation of segmented upload step (see above)
TEMPORARY_URL = "http://example.com/temporary_url"

upload_status = client.segmented_upload_status(TEMPORARY_URL)

print(upload_status.received)
print(upload_status.expecting)
print(upload_status.size)
print(upload_status.segment_size)
```

* Deposit a file uploaded by segments

```python
from sword3client import SWORD3Client
client = SWORD3Client()

SERVICE = "http://example.com/service-document"

# Temporary URL obtained from initialisation of segmented upload step (see above)
TEMPORARY_URL = "http://example.com/temporary_url"

resp = client.create_object_with_temporary_file(SERVICE, 
                                                TEMPORARY_URL, 
                                                "test.zip", 
                                                "application/zip")
```
