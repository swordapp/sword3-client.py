from sword3common import Metadata

class ContentMalformedMetadata(Metadata):
    @property
    def data(self):
        return "a random stream of characters that aren't JSON metadata"