import logging
import tempfile
from ebmeta import shell
from . import Ebook

log = logging.getLogger('mobi')

class Pdf(Ebook):
    def __init__(self, path):
        self.type = 'pdf'
        self.__content_opf_str = None
        super(Pdf, self).__init__(path)

    def __get_content_opf_str(self):
        if self.__content_opf_str: return self.__content_opf_str

        with tempfile.NamedTemporaryFile() as f:
            shell.pipe(["ebook-meta", "--to-opf=" + f.name, self.path])
            self.__content_opf_str = unicode(f.read(), "utf_8", "replace")

        return self.__content_opf_str

    content_opf_str = property(__get_content_opf_str)
