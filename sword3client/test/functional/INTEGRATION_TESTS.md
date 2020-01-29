# Invenio Integration Tests

The file `test_invenio.py` contains integration tests that demonstrate the
behaviours of SWORDv3 that are implemented by this client, acting against a
live, running, Invenio instance.

This document outlines the tests, the behaviours they are testing, and the 
sections of the [SWORDv3 behaviours](https://swordapp.github.io/swordv3/swordv3-behaviours.html) 
that they cover.

Note that each test can also be run in `MOCK_MODE` to check that the client and the
tests themselves are behaving.


## 1. Retrieve Service Document

Make a request against a given `SERVICE_URL` and verify that we retceive a `ServiceDocument`
object that validates against the correct structure.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#1.


## 2. Create and Retrieve with Metadata

We create an object with only metadata by sending a SWORD Metadata formatted document to 
the `SERVICE_URL`.  We expect to receive a `StatusDocument` from a successful deposit
(which validates against the correct structure),
with a status code of `201` (Created), and a `Location` header giving us the `Object-URL`

We then verify that this metadata-only object has been correctly deposited in Invenio by making
a `GET` request against the `Object-URL` that we find in the `StatusDocument`.  We verify
again that this document meets the structural requirements, and verify that the contents of the
retrieved status document are the same as the one we were given in the first operation, and that
a `Metadata-URL` is available to us.

Finally we `GET` the `Metadata-URL` to retrieve the metadata we originally deposited.  We verify
that it meets the correct structure, and that the metadata we deposited is reflected back to us.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.1.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#3.1.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#3.2.


## 3. Create Object with Binary

We create an object with an opaque binary stream (i.e. not a package) by sending a stream of bytes
to the `SERVICE_URL`.  We expect to receive a `StatusDocument` from a successful deposit (which
validates against the correct structure), with a status code of `201` (created), and a `Location` header
giving us the `Object-URL`.

We then look in the `links` section of the `StatusDocument` to find the link to the file we created
and then we `GET` that `File-URL` to retrieve the bytes stored by the server.  We confirm that they
bytes retrieved from the server match the bytes that we sent in the originla request.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.4.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#3.3.


## 4. Create Object with Package

We create an object with a SWORDBagIt package by sending the stream of bytes
to the `SERVICE_URL`.  We expect to receive a `StatusDocument` from a successful deposit (which
validates against the correct structure), with a status code of `201` (created), and a `Location` header
giving us the `Object-URL`.

We then look in the `links` section to find the `origianlDeposit` package zip file, and confirm
it is represented correctly.  We then `GET` that `File-URL` and confirm that the contents are
the same as the contents we originally deposited.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.5.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#3.4.


## 5. Append Metadata, then Binary, then a Package

We start by creating an object with metadata, as per (1), so we have a metadata-only record in
Invenio that we can work with.

We then create a SWORD default metadata document with some additional metadata fields in it, and
`POST` it to the `Object-URL`.  We expect to get a `200`, a `Location` header for the `Object-URL`
and a valid `StatusDocument` (Note: we expect this part of the specification to change, based on the feedback
from this development work).

Next we `GET` the metadata that the server holds, from the `Metadata-URL`, and confirm that the
metadata that is returned is a combination of the metadata provided in the original request and
the metadata sent in the second request.

Now we append an opaque binary stream (i.e. not a package) by sending a stream of bytes
to the `Object-URL`.  We expect to receive a valid `StatusDocument` from a successful deposit, 
with a status code of `200`, and a `Location` header
giving us the `File-URL`. (Note: we expect this part of the specification to change, based on the feedback
from this development work).

To confirm that the file has been appended, we get the `File-URL` from the `Location` header and
`GET` it from Invenio.  We then confirm that the downloaded bytes are the same as the originally
uploaded bytes.

Finally we append a SWORDBagIt package by `POST` to the `Object-URL`.  We expect to get a `200`, a `Location` header for the `Object-URL`
and a valid `StatusDocument` (Note: we expect this part of the specification to change, based on the feedback
from this development work).  We confirm that this `originalDeposit` is in the `links` section
of the `StatusDocument`, but we do not attempt to download the package, as we have verified file
and package downloads elsewhere in these tests.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.1.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.4.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.5.

## 6. Replace Metadata and Binary Content

We start by creating an object with metadata, as per (1), so we have a metadata-only record in
Invenio that we can work with.  Then we append a binary file to it as per (5) so the record has both
metadata and files.

We then create a SWORD default metadata document with some additional metadata fields in it, and
`PUT` it to the `Metadata-URL`.  We expect to get a `204`, a `Location` header for the `Metadata-URL`
and an empty request body (Note, this response format may change based on feedback from this development)

To confirm that the metadata has been updated, we `GET` the `Metadata-URL` and confirm that the
metadata provided in the orignal deposit has gone, and the new metadata provided in the second
request is present.

Next we replace the binary file, by sending a new stream of opaque bytes to the `File-URL` (which
came from the `Location` header of the append operation above).

To confirm that the file was replaced, we then `GET` the same `File-URL`, and confirm that the bytes
we retrieve are the bytes that we send in the replacement operation.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.1.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.2.

## 7. Replace fileset with Binary Content

We start by creating a record with a single binary file as per (3), then we append a second binary
file as per (5).  This gives us a record in Invenio with 2 binary files that we can work with.

Now we send a third binary stream put `PUT` to the `FileSet-URL` (which is retrieved from the
status document in the original deposit operation).  We expect a `204` response.

We then retrieve the `StatusDocument` again, and confirm that there is only one `originalDeposit`
and no other files attached to the object.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.6.


## 8. Replace the Object with Metadata, then Binary Content, then a Package

We start by creating an object with metadata, as per (1), so we have a metadata-only record in
Invenio that we can work with. 

We then replace the entire object by `PUT` to the `Object-URL` with an opaque binary stream.  We
then retrieve the object by `GET` to the `Object-URL` and confirm that there is a single file in the 
`links`.  We go on to retrieve the metadata by `GET` to the `Metadata-URL` and confirm that the
metadata we created the record with is gone.  This demonstrates that all the original content and
metadata of the item has been replaced with a single binary file.

Next we replace the object again, with metadata-only by constructing a default SWORD metadata document
and doing `PUT` to the `Object-URL` with it.  We then retrieve the new `StatusDocument` by `GET` to
the `Object-URL` and confirm that the file which was previously present is gone.  We retrieve
the metadata again, and confirm that this is the metadata we just sent.

Finally we replace the object with a package by sending a SWORDBagIt package via `PUT` to the 
`Object-URL`.  We then retrieve the latest `StatusDocument` as above and confirm that the zip file
is listed as an `originalDeposit`.  We also confirm the metadata has gone by retrieving the metadata
again, and checking that the previously deposited metadata has gone.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.8.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.11.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.12.


## 9. Delete on all levels of the Object

 We start by creating an object with metadata, as per (1) and then adding two binary files as per 
 (5), giving us an object with metadata and 2 files in Invenio to work with.
 
 First we delete the metadata by sending `DELETE` to the `Metadata-URL`.  Then confirm that the metadata
 has gone by `GET` to the `Metadata-URL` (which will still exist, even though `DELETE` has run), and
 confirming that the metadata record is empty.
 
 Next we delete one of the files by sending `DELETE` to the `File-URL`.  Then confirm that the file
 has gone by `GET` to the `Object-URL` and checking the `links` to see that only one file remains.
 
 Now we delete the entire fileset, by sending `DELETE` to the `FileSet-URL`.  Then confirm that all
 remaining files have gone by `GET` to the `Object-URL` and checking the `links` to see that 
 no files remain.
 
 Finally we delete the entire object by `DELETE` to `Object-URL`, then confirm by attempting and
 failing to `GET` on `Object-URL`.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#6.1.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#6.2.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#6.3.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#6.4.
