"""Edit metadata using zenity."""

from BeautifulSoup import BeautifulStoneSoup, Tag
import logging
import yaml
from zipfile import ZipFile
import ebmeta
from ebmeta import shell
from ebmeta import template
from ebmeta.actions import backup
from ebmeta.ebook import ebook_factory
from ebmeta.yamlwriter import opf_to_yaml
from ebmeta.zenity import edit_string, ZenityCancelled

log = logging.getLogger('display')

def run(new_yaml_text=None):
    """Run this action."""

    path = ebmeta.arguments.filename
    ebook = ebook_factory(path)
    opf = ebook.opf
    template_str = template.get_file_content("{}.yaml".format(ebook.type))
    yaml_text = opf_to_yaml(opf, template_str)

    if new_yaml_text:
        result = new_yaml_text
    else:
        try:
            result = edit_string(yaml_text)
        except ZenityCancelled:
            log.debug("Operation was cancelled.")
            return

    if result.strip() == yaml_text.strip():
        log.debug("No change was made.")
    elif result:
        log.debug("Writing changes to ebook file.")
        d1 = yaml.load(yaml_text)
        d2 = yaml.load(result)
        if (ebook.type == 'epub') and (not d2.get('uuid')):
            # ensure the new metadata has a uuid
            d2['uuid'] = ebmeta.new_id()
        changes = dict()
        for key in d2.keys():
            if key == 'description':
                if (d1[key] or "").strip() != (d2[key] or "").strip(): changes[key] = d2[key]
            if key == 'authors':
                if d1[key] != d2[key]:
                    changes[key] = d2[key]
                    if d2.has_key('author sort'): changes['author sort'] = d2['author sort']
            if key == 'title':
                if d1[key] != d2[key]:
                    changes[key] = d2[key]
                    if d2.has_key('title sort'): changes['title sort'] = d2['title sort']
            else:
                if d1[key] != d2[key]: changes[key] = d2[key]
        log.debug("The following keys changed: %s", ' '.join(changes.keys()))

        backup.run() # backup only if backup doesn't exist

        if ebook.type == 'pdf':
            write_changes_pdf(ebook, changes)
        else:
            write_changes(ebook, changes)

def write_changes(ebook, changes):
    """Write the metadata in the given dictionary into the ebook file."""

    path = ebmeta.arguments.filename

    for key in changes.keys():
        if changes[key] == None: changes[key] = ""

    args = [
        "ebook-meta",
        '"{}"'.format(path)
    ]
    for a, b in (
        ('authors',       'authors'),
        ('book-producer', 'book producer'),
        ('isbn',          'isbn'),
        ('language',      'language'),
        ('date',          'publication date'),
        ('publisher',     'publisher'),
        ('series',        'series'),
        ('title',         'title')
    ):
        if changes.has_key(b): args.append(u"--{}=\"{}\"".format(a, quote(changes[b])))

    for a, b in (
        ('rating',        'rating'), # rating can't be unset once it's set, from ebook-meta CLI
        ('index',         'series index'), # series index can't be unset either
        ('author-sort',   'author sort'),
        ('title-sort',    'title sort')
    ):
        if changes.has_key(b):
            if changes[b]:
                args.append(u"--{}=\"{}\"".format(a, quote(changes[b])))

    if changes.has_key('description'):
        description = shell.pipe(["pandoc"], changes['description'])
        args.append(  u"--comments=\"{}\"".format(quote(description))  )

    if changes.has_key('tags'):
        args.append(  u"--tags=\"{}\"".format(quote(','.join(changes['tags'])))  )

    if len(args) > 2:
        # Run ebook-meta
        # shell.run(" ".join(args), shell=True)
        shell.pipe(" ".join(args), shell=True)

    if ebook.type == 'epub':
        # set uuid only for Epub files
        if(changes.has_key('uuid')):
            try:
                setUuid(changes['uuid'])
            except:
                pass

def setUuid(uuid_txt):
    """Write a new uuid to the Epub file."""

    path = ebmeta.arguments.filename

    metadata = None
    metapath = "content.opf"
    with ZipFile(path, 'r') as zip:
        try:
            metadata = zip.read(metapath)
        except KeyError:
            metapath = "OEBPS/content.opf"
            metadata = zip.read(metapath)

    log.debug("new uuid: %s", uuid_txt)

    soup = BeautifulStoneSoup(metadata)
    id = (
        soup.find('dc:identifier', attrs={'opf:scheme':'uuid'}) or
        soup.find('dc:identifier', attrs={'opf:scheme':'UUID'}) or
        soup.find('dc:identifier', attrs={'scheme':'uuid'}) or
        soup.find('dc:identifier', attrs={'scheme':'UUID'})
    )
    if not id:
        m = soup.find('metadata')
        id = Tag(soup, 'dc:identifier')
        id['id'] = 'uuid_id'
        id['opf:scheme'] = 'uuid'
        id.insert(0, "--")
        m.insert(0, id)
    id.contents[0].replaceWith(unicode(uuid_txt))

    #[node.extract() for node in id.findAll()] # remove contents
    #id.insert(0, uuid) # insert uuid

    shell.run(["zip", "-d", path, metapath])
    with ZipFile(path, 'a') as zip:
        zip.writestr(metapath, str(soup))

def quote(text):
    """Change " to \\"."""

    try:
        return unicode(text, errors='replace').replace('"', '\\"')
    except TypeError:
        return text

def write_changes_pdf(ebook, changes):
    """Write the metadata in the given dictionary into the pdf file."""

    path = ebmeta.arguments.filename

    for key in changes.keys():
        if changes[key] == None: changes[key] = ""

    args = [
        "exiftool",
        '"{}"'.format(path)
    ]
    for a, b in (
        ('Author', 'authors'),
        ('Title',  'title')
    ):
        if changes.has_key(b): args.append("-{}=\"{}\"".format(a, quote(changes[b])))

    if len(args) > 2:
        # Run ebook-meta
        # shell.run(" ".join(args), shell=True)
        shell.pipe(" ".join(args), shell=True)
