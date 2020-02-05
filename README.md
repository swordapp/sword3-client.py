# SWORDv3 Client

This client library provides all the basic features of SWORDv3 as a Python API.

## Usage

Create a new instance of the client

```
from sword3client import SWORD3Client
client = SWORD3Client()
```

See the object definitions for full details of all operations available.  Examples of common usage would be:

* Create an object with metadata only:

```
SERVICE = "http://example.com/service-document"
metadata = Metadata()
metadata.add_dc_field("creator", "Test")
response = client.create_object_with_metadata(SERVICE, metadata)
```

* Create an object with a package:

```
package_path = "/path/to/file.zip"
digest = {sword3common.constants.DIGEST_SHA_256: "digest...."}
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

```
OBJ_URL = "http://example.com/object/1"
status = client.get_object(OBJ_URL)
```

* Append a binary file:

```
OBJ_URL = "http://example.com/object/1"
file_path = "/path/to/binary.bin"
digest = {sword3common.constants.DIGEST_SHA_256: "digest...."}
with open(file_path, "rb") as stream:
  response = client.add_binary(OBJ_URL, stream, "test.bin", digest)
```

* Delete the object:

```
OBJ_URL = "http://example.com/object/1"
response = client.delete_object(OBJ_URL)
```
