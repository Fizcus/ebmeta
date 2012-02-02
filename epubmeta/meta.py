"""Epub metadata."""

import datetime
from BeautifulSoup import BeautifulStoneSoup
import re
import logging
from string import Template
import yaml
from epubmeta import shell
from epubmeta import template

log = logging.getLogger('meta')

months = "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sept,Oct,Nov,Dec".split(',')

def getAttr(soup, attr):
    try:
        return soup[attr]
    except:
        return None
def getStr(soup):
    try:
        return soup.string
    except:
        return None

isodate = re.compile("([\d]+)-([\d]+)-([\d]+)")
def formatDate(txt):
    m = isodate.match(txt)
    if not m: return None
    return "{} {} {}".format(
        m.group(3),
        months[int(m.group(2)) - 1],
        m.group(1)
    )

def htmlToMarkdown(txt):
    return shell.pipe(["pandoc", "--no-wrap", "--from", "html", "--to", "markdown"], txt).strip()

yamlSimple = re.compile("^[A-Za-z0-9\.]+$")
yamlNewline = re.compile("^", re.MULTILINE)
def yamlValue(txt, multiline=False):
    if txt == None: return '~'
    if len(txt) == 0: return '~'
    if type(txt) is list:
        return '[' +   ', '.join(yamlValue(x) for x in txt)   + ']'
    if yamlSimple.match(txt): return txt
    if multiline:
        return "|\n" + yamlNewline.sub("  ", txt)
    else:
        return '"' + txt.replace('"', '\\x22') + '"'

class Metadata(dict):
    def __init__(self, txt):
        if txt[:100].find("<?xml") >= 0:
            self.init_opf(txt)

    def init_opf(self, txt):
        soup = BeautifulStoneSoup(txt, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
        self['title'] = getStr(soup.find('dc:title'))
        self['title sort'] = getAttr(soup.find('meta', attrs={'name':'calibre:title_sort'}), 'content')
        authors = soup.findAll('dc:creator', attrs={'opf:role':'aut'})
        self['authors'] = " & ".join([getStr(author) for author in authors])
        self['author sort'] = getAttr(authors[0], 'opf:file-as')
        self['publication date'] = formatDate( getStr(soup.find('dc:date')) )
        self['publisher'] = getStr(soup.find('dc:publisher'))
        self['book producer'] = getStr( soup.find('dc:contributor', attrs={'opf:role':'bkp'}) )
        self['isbn'] = (
            getStr( soup.find('dc:identifier', attrs={'opf:scheme':'ISBN'}) ) or
            getStr( soup.find('dc:identifier', attrs={'opf:scheme':'isbn'}) )
        )
        self['language'] = getStr(soup.find('dc:language'))
        self['rating'] = getAttr(soup.find('meta', attrs={'name':'calibre:rating'}), 'content')
        self['series'] = getAttr(soup.find('meta', attrs={'name':'calibre:series'}), 'content')
        self['series index']  = getAttr(soup.find('meta', attrs={'name':'calibre:series_index'}), 'content')
        self['uuid'] = (
            getStr(soup.find('dc:identifier', attrs={'opf:scheme':'uuid'})) or
            getStr(soup.find('dc:identifier', attrs={'opf:scheme':'UUID'}))
        )
        tags = soup.findAll('dc:subject')
        self['tags'] = []
        if tags:
            self['tags'] = [getStr(x) for x in tags]
            #self['tags'] = ", ".join([getStr(x) for x in tags])
        description = getStr(soup.find('dc:description'))
        self['description'] = htmlToMarkdown(description)

    def __unicode__(self):
        txt = []
        key_width = 0
        keys = self.keys()
        keys.sort()

        for key in keys:
            if len(key) > key_width: key_width = len(key)

        for key in keys:
            if key == 'tags': value = ", ".join(self['tags'])
            else: value = self[key]

            txt.append("{}: {}".format(key.ljust(key_width, ' '), value))

        return "\n".join(txt)

    def yaml(self):
        templ = template.get_file_content('metadata.yaml')
        d = dict()
        for key in self.keys():
            d[key.replace(' ', '_')] = yamlValue(self[key], key == 'description')
        return Template(templ).substitute(d)
