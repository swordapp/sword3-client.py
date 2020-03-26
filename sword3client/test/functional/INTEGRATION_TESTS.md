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


## 10. Create an Object By Reference

We take a file that is hosted on github, and we create a ByRereference model object linking to it.

We send that request by sending a `POST` to the `Service-URL`.  Then we confirm that the correct 
create response is received, and that we have a Status Document given back to us.

To further check, we retrieve the Status Document again from the server and then confirm that there
is a "ByReference" deposit listed as the only "Original Deposit".

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.2.


# 11. Create an Object with Metadata and By Reference Files

This test combines features from (2) and (10) above into a single request.

We create a metadata record and a ByReference list of files, and we bundle them together in the
single "Metadata and By Reference" document format.

We then issue a `POST` against the `Service-URL` with the MD+BR document, and confirm that we get a
suitable response code and a Status Document.  We then retrieve the object from the server again,
and use the response to verify that there is a single "Original Deposit" that is a "By Reference"
file.  We go on to retrieve the metadata document and confirm that the metadata we sent in the
create request is present.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.3.


## 12. Upload a large file in segments to a temporary location

We start by initialising a segmented upload request with the server, indicating a file size, number
of segments to upload, and how large each of those segments will be.  The server respons by giving
us a `Temporary-URL` to which we can upload the file segments.

To test the ability of the endpoint to handle arbitrary segments, we take a file in the format of 
a SWORDv3 BagIt, and we divide it into 5 segments, and we send only 2 of them.

Once those uploads have completed, we perform a `GET` on the `Temporary-URL` to get a status report
on the segmented upload.  We check to confirm that it has received two of the segments and is
expecting/awaiting the remaining ones.

Finally we verify that it's possible to abort a segmented upload by issuing a `DELETE` on the
`Temporary-URL`.  We then attempt to `GET` the `Temporary-URL` again and conform that we are unable to.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#7.1.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#7.2.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#7.3.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#7.4.


## 13. Upload a large file and then deposit it

This test looks at the connection between uploading a large file to a temporary location and then
depositing that large file to the repository.

We start by creating a file at a `Temporary-URL` as per (12).  We upload all file segments.

We then `POST` to the `Service-URL` using the `Temporary-URL` as the location of the file in
a "By Reference" deposit (the details of which are handled for us in client).

In the response to the deposit we receive a Service Document, and we check in that document that
there is a "By Reference" deposit as the only "Original Deposit", and that it references the 
`Temporary-URL` that we uploaded the large file to.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#2.6.


## 14. Append By Reference (both files and metadata+files)

To initialise this test we first create a new object in the repository as metadata-only, as 
per (2).

Then we create a By Reference model object pointing to a file hosted in github, and we append it
to the object we created by `POST` to the `Object-URL`.  We confirm that we receive the correct
response code, and a Status Document.  We then look in the status document to ensure that there
is a single "Original Deposit" file, which is marked as "By Reference".

Next we create a "Metadata And By Reference" model object, pointing to a new file also hosted in
github, and we provide some new metadata elements.  We append that to the object too by `POST`
to the `Object-URL` again.

To confirm the second append has worked correctly, we check the Status Document again, expecting
for there to be 2 "Original Deposit" files (one for each By Reference append), both of which
are marked as "By Reference".  We then download the metadata record for the object, and confirm
that the resulting metadata is the combination of the metadata that was uploaded.


**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.2.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.3.


## 15. Append a large file

This test is similar to (14) but uses a Segmented Upload file to demonstrate integration with
that feature.

We start by creating a new object in the repository as metadata-only, as per (2).

Then we initialise a Segmented Upload and upload all the segments of our test file to the `Temporary-URL`
as per (13).  We then deposit the temporary file in the same was as a regular "By Reference" file,
which the client handles for us for our convenience.

We confirm that the deposit operation returns a suitable error code, and then we check that
the "Original Deposit" record in the Status Document is for a "By Reference" file that refers to
our `Temporary-URL`.

We then perform both of the above operations again (upload temporary file and append it), 
but this time we identify the large file as a "package".  When we check the "Original Deposit"
records in the Status Document, we expect there to be 2 "By Reference" files.  One of those files
is expected to have the `packaging` property set, while the other is not.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.6.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#4.7.


## 16. Replace individual files and all files By Reference

This tests our ability to replace individual files, or all files (the fileset) with one or more files
by reference.

We start by creating a basic object with a binary file, as per (3).  We take the `File-URL` for
that file from the Status Document, and then we issue a `PUT` to that `File-URL` with a By Reference
document, containing a reference to a file hosted on github.

Once that operation completes, we retrive the Status Document from the server, and check that
the original binary file we created the object with has gone.  We also check that there is now
a single "Original Deposit" file, which is marked as a "By Reference" file, pointing to the file
hosted on github.

Next we construct a new By Reference deposit containing two file references, to files hosted on
github.  We then issue a `PUT` request to the `Fileset-URL` with this By Reference document.

Finally, to confirm that operation completed successfully, we request the object and check that the
fileset now contains those two files.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.3.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.5.


## 17. Replace individual file with a large file

This is very similar to (16) and exists to cover the case where a large file has been uploaded
to a `Temporary-URL` before being deposited By Reference to replace an individual file.

We start by creating a basic object with a binary file, as per (3).  

Next we initialise and carry out a segmented upload, as per (12) and (13).

We take the `File-URL` for the original binary file from the Status Document, and then we issue 
a `PUT` to that `File-URL` with a By Reference document, containing a reference to the `Temporary-URL`
(the client handles this for us).

Finally, we retrieve the up-to-date Status Document from the server, and confirm that there is
a single "Original Deposit", and it is marked as "By Reference", and links to our `Temporary-URL`.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.4.


## 18. Replace the FileSet with a large file

This is similar to the second part of (16) and exists to cover the case where a large file has been
uploaded to a `Temporary-URL` before being deposited By Reference to replace all the files in the
fileset.

We start by creating a basic object with a binary file, as per (3).  We then append a binary file
to it, so there are multiple files in the item, as per (5).

Next we initialise and carry out a segmented upload, as per (12) and (13).

We then issue a `PUT` to the `FileSet-URL` with a "By Reference" deposit using the `Temporary-URL`
of the large file.

In order to verify the action has worked correctly, we retrieve the Status Document for the 
object, and check that there is now only one "Original Deposit", and that it is marked as a
"By Reference" file, with a reference to the `Temporary-URL`.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.7.


## 19. Replace entire object with new metadata and files by reference

First we create an object with some existing metadata and binary files, by creating an object
with metadata as per (2) and then appending a binary file as per (5).

For our first test in this section we replace the entire object with only By Reference files.  We
construct a By Reference deposit with two file links, hosted on github.  We then issue a `PUT` on
the `Object-URL` with that By Reference document.  The repsonse contains the up-to-date Status
Document, and we check it to ensure that it contains the two files that were in the By Reference
document.  Then we `GET` the `Metadata-URL`, which we expect to be empty, or at least no longer
to contain the metadata we created the object with.

The next test replaces the entire object with both metadata and by reference files.  We create a
By Reference document for a single file (hosted on github) and a short metadata document, and we
combine them into a "Metadata and By Reference" document.  We then issue a `PUT` on the `Object-URL`
with that document.  The response contains the up-to-date Status Document, and we check it to 
ensure that there is only one "Original Deposit" which is the file in the most recent By Reference
document.  We then retrieve the metadata and confirm that the metadata we just sent is reflected
back at us.

**Areas of spec explicitly tested:**

* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.9.
* https://swordapp.github.io/swordv3/swordv3-behaviours.html#5.10.


## 20. Replace entire object with a single large file

This is very similar to the first part of (19) and demonstrates that process with a large file
uploaded to a `Temporary-URL`.

First we create an object with some existing metadata and binary files, by creating an object
with metadata as per (2) and then appending a binary file as per (5).

Next we initialise and carry out a segmented upload, as per (12) and (13).

We then replace the entire object with the large file with a `PUT` to the `Object-URL` with a
By Reference deposit using the `Temporary-URL`.

To confirm success we check for a suitable status code response and look to see that the object
has only a single "Original Deposit", marked as a "By Reference" file with a reference to the
`Temporary-URL`.  We do not check for metadata removal, as this is tested in (19).

We then carry out the steps above again, and this time when we do the deposit we also indicate that
the large file is a packaged file.  When we confirm that the file has been successfully deposited
we also confirm that the file record has the correct packaging recorded against it.