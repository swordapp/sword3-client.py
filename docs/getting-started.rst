Getting Started
===============

Installation
------------

You can install the SWORDv3 client from PyPI as `sword3client
<https://pypi.org/project/sword3client/>`_.

Creating a deposit
------------------

Here's an example of usage, to create a deposit with metadata and a single file:

.. code:: python

   from sword3client import SWORD3Client
   from sword3common import Metadata

   metadata = Metadata()
   metadata.add_dc_field("creator", "Smith, J.")
   metadata.add_dcterms_field("license", "https://creativecommons.org/licenses/by-sa/4.0/")
   metadata.add_field("custom", "entry")

   client = SWORD3Client()
   dr = client.create_object_with_metadata(SERVICE_URL, metadata, in_progress=True)

   with open('data-table.csv') as f:
       sha256 = hashlib.sha256()
       for chunk in iter(lambda: f.read(4096), b""):
           sha256.update(chunk)

       content_length = f.tell()
       f.seek(0)

       digest = {constants.DIGEST_SHA_256: sha256.digest()}

       client.add_binary(
           dr.status_document,
           f,
           'data-table.csv',
           digest,
           content_length,
           content_type="text/csv",
           in_progress=True,
       )
