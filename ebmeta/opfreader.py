"""Ebook metadata."""

import datetime
from BeautifulSoup import BeautifulStoneSoup
import re
import logging
from ebmeta import shell
from ebmeta import template

log = logging.getLogger('opfreader')

months = u"Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sept,Oct,Nov,Dec".split(',')

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
    if not txt: return None
    m = isodate.match(txt)
    if not m: return None
    return u" ".join((
        m.group(3),
        months[int(m.group(2)) - 1],
        m.group(1)
    ))

def htmlToMarkdown(txt):
    if not txt: return txt
    return shell.pipe(["pandoc", "--no-wrap", "--from", "html", "--to", "markdown"], txt).strip()

class Opf(dict):
    def __init__(self, txt):
        if not (txt[:100].find("<?xml") >= 0):
            raise ValueError("Not an XML stream.")

        soup = BeautifulStoneSoup(txt, convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
        self[u'title'] = getStr(soup.find('dc:title'))
        self[u'title sort'] = getAttr(soup.find('meta', attrs={'name':'calibre:title_sort'}), 'content')
        authors = (
            soup.findAll('dc:creator', attrs={'opf:role':'aut'}) or
            soup.findAll('dc:creator', attrs={'role':'aut'})
        )
        self[u'authors'] = None
        self[u'author sort'] = None
        print len(authors)
        print authors[0]
        if authors and len(authors):
            self[u'authors'] = u" & ".join([x for x in [getStr(author) for author in authors] if x is not None])
            self[u'author sort'] = (
                getAttr(authors[0], 'opf:file-as') or
                getAttr(authors[0], 'file-as')
            )
        self[u'publication date'] = formatDate( getStr(soup.find('dc:date')) )
        self[u'publisher'] = getStr(soup.find('dc:publisher'))
        self[u'book producer'] = (
            getStr( soup.find('dc:contributor', attrs={'opf:role':'bkp'}) ) or
            getStr( soup.find('dc:contributor', attrs={'role':'bkp'}) )
        )
        self[u'isbn'] = (
            getStr( soup.find('dc:identifier', attrs={'opf:scheme':'ISBN'}) ) or
            getStr( soup.find('dc:identifier', attrs={'opf:scheme':'isbn'}) ) or
            getStr( soup.find('dc:identifier', attrs={'scheme':'ISBN'}) ) or
            getStr( soup.find('dc:identifier', attrs={'scheme':'isbn'}) )
        )
        if not self[u'isbn']:
            for bookid in [getStr(x) for x in soup.findAll('dc:identifier')]:
                if bookid and ('isbn' in bookid.lower()):
                    self[u'isbn'] = bookid.split(':')[-1]
        self[u'language'] = getStr(soup.find('dc:language'))
        self[u'rating'] = getAttr(soup.find('meta', attrs={'name':'calibre:rating'}), 'content')
        self[u'series'] = getAttr(soup.find('meta', attrs={'name':'calibre:series'}), 'content')
        self[u'series index']  = getAttr(soup.find('meta', attrs={'name':'calibre:series_index'}), 'content')
        self[u'uuid'] = (
            getStr(soup.find('dc:identifier', attrs={'opf:scheme':'uuid'})) or
            getStr(soup.find('dc:identifier', attrs={'opf:scheme':'UUID'})) or
            getStr(soup.find('dc:identifier', attrs={'scheme':'uuid'})) or
            getStr(soup.find('dc:identifier', attrs={'scheme':'UUID'}))
        )
        tags = soup.findAll('dc:subject')
        self[u'tags'] = []
        if tags:
            self[u'tags'] = [getStr(x) for x in tags]
            #self['tags'] = ", ".join([getStr(x) for x in tags])
        description = getStr(soup.find('dc:description'))
        self[u'description'] = htmlToMarkdown(description)

    def __unicode__(self):
        txt = []
        key_width = 0
        keys = self.keys()
        keys.sort()

        for key in keys:
            if len(key) > key_width: key_width = len(key)

        for key in keys:
            if key == 'tags': value = u", ".join(self[u'tags'])
            else: value = self[key]

            #print "key: " + key.__class__.__name__ + " : " + key
            #print "value: " + value.__class__.__name__
            txt.append(u"{}: {}".format(key.ljust(key_width, u' '), value))

        return u"\n".join(txt)
