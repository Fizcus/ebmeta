import logging
import tempfile
from zipfile import ZipFile
from ebmeta import shell
from . import Ebook

log = logging.getLogger('epub')

class Epub(Ebook):
    def __init__(self, path):
        self.type = 'epub'
        self.__content_opf_str = None
        super(Epub, self).__init__(path)

    def __get_content_opf_str(self):
        if self.__content_opf_str: return self.__content_opf_str

        try:
            with ZipFile(self.path, 'r') as zip:
                try:
                    self.__content_opf_str = zip.read("content.opf")
                except KeyError:
                    self.__content_opf_str = zip.read("OEBPS/content.opf")
            return self.__content_opf_str
        except:
            pass

        # give up and use the ebook-meta to get the metadata
        with tempfile.NamedTemporaryFile() as f:
            shell.pipe(["ebook-meta", "--to-opf=" + f.name, self.path])
            self.__content_opf_str = f.read()

        return self.__content_opf_str

    content_opf_str = property(__get_content_opf_str)