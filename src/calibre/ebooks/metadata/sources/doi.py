#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2014, sengian <sengian1 at gmail.com>'
__docformat__ = 'restructuredtext en'

from urllib import quote as url_quote
from urllib2 import HTTPError
from lxml import etree

from calibre.ebooks.chardet import xml_to_unicode
from calibre.ebooks.metadata import check_doi, check_isbn
from calibre.ebooks.metadata.sources.base import Source
from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.icu import lower
from calibre.utils.cleantext import clean_ascii_chars
from calibre.utils.date import parse_only_date

# An ordered list of the preferred content type for metadata retrieval
_ORDERED_CONTENT_TYPES = ['application/vnd.crossref.unixref+xml',
                    'application/vnd.datacite.datacite+xml', 'application/rdf+xml']

def author_unixref(author):
    given_name = author.findtext('given_name', default='')
    surname = author.findtext('surname', default='')
    if given_name:
        return '%s %s' % (given_name, surname)
    else:
        return surname

def date_unixref(pubdate):
    month = pubdate.findtext('month', default='')
    year = pubdate.findtext('year', default='')
    date = year
    if month:
        date = year+'/'+month
    return parse_only_date(date, assume_utc=True)

class DOI(Source):

    name = 'DOI'
    author = 'Sengian'
    description = _('Downloads metadata from doi.org')

    capabilities = frozenset(['identify'])
    touched_fields = frozenset(['title', 'authors', 'identifier:doi'
        'identifier:url', 'pubdate', 'languages', 'publisher'])
    supports_gzip_transfer_encoding = True
    add_browser_extra_headers = [('accept', ', '.join(_ORDERED_CONTENT_TYPES))]
    # Shortcut, since we have no cached cover URLS
    cached_cover_url_is_reliable = False

    def __init__(self, *args, **kwargs):
        Source.__init__(self, *args, **kwargs)

    def create_query(self, identifiers={}): # {{{
        base_url = 'http://dx.doi.org/'
        doi = check_doi(identifiers.get('doi', None))
        if doi is not None:
            q = doi
        else:
            return None

        if isinstance(q, unicode):
            q = q.encode('utf-8')
        return base_url + url_quote(q)
    # }}}

    def identify(self, log, result_queue, abort, title=None, authors=None, # {{{
            identifiers={}, timeout=30):

        query = self.create_query(identifiers=identifiers)
        if not query:
            err = 'No valid DOI found for this item'
            log.error(err)
            return err

        try:
            content_type, xml_tree = self.make_query(query, log, timeout=timeout)
        except:
            err = 'Failed to make query to doi.org, aborting.'
            log.exception(err)
            return err

        if xml_tree is not None and not abort.is_set():
            # Parse the result and put it in the queue
            # log.error(etree.tostring(xml_tree, pretty_print=True, with_tail=True, method='xml'))
            result = self.parse_feed(content_type, xml_tree, log)
            if result is not None:
                result = clean_downloaded_metadata(result)
                result_queue.put(result)
 
    def parse_feed(self, content_type, tree, log):
        # Determine the type of content
        if content_type == 'application/vnd.crossref.unixref+xml':
            # Crossref unixref
            contents = self.parse_unixref(tree, log)
        elif content_type == 'application/vnd.datacite.datacite+xml':
            # DataCite Metadata Schema
            contents = self.parse_datacite(tree, log)
        elif content_type == 'application/rdf+xml':
            # Simple rdf/xml
            contents = self.parse_rdf(tree, log)
        else:
            # Unknown content, theoretically impossible
            err = 'Unknown content type sent by the server, weird!'
            log.error(err)
            return None

        title = None
        if contents['title']:
            title = contents['title']
        authors = []
        if contents['authors']:
            authors = contents['authors']
        mi = Metadata(title, authors)
        # log.error(repr(contents))
        return mi

    def parse_unixref(self, tree,log):
        # Parse an Unixref Crossref xml
        # Scheme: http://doi.crossref.org/schemas/unixref1.1.xsd
        contents = {}
        # Title
        title = tree.xpath('.//titles/title')
        if title:
            contents['title'] = [elt.text.strip() for elt in title]
            if len(contents['title'])<2:
                contents['title'] = contents['title'][0]
        # Authors
        authors = tree.xpath('.//contributors')
        if authors and authors[0].getchildren():
            contents['first_author'] = author_unixref(authors[0].xpath('descendant::person_name[@sequence="first"]')[0])
            contents['authors'] = [author_unixref(aut) for aut in authors[0].iterchildren(tag='person_name')]
        # Journal
        journal = tree.xpath('.//journal/journal_metadata')
        if journal:
            journal_data = {
                            'full_journal_title':'full_title',
                            'abbrev_journal_title':'abbrev_title',
                            'issn_print_journal':'issn[@media_type="print"]',
                            'issn_electronic_journal':'issn[@media_type="electronic"]',
                            'coden_journal':'coden'
                            }
            for k,xpathexp in journal_data.iteritems():
                elt = journal[0].xpath('descendant::%s'%(xpathexp,))
                if elt:
                    contents[k] = elt[0].text.strip()
        issue = tree.xpath('.//journal/journal_issue')
        if issue:
            pub_date = journal[0].xpath('descendant::publication_date[@media_type="print"]')
            if pub_date:
                contents['publication_date'] = date_unixref(pub_date[0])
            volume = journal[0].xpath('descendant::journal_volume/volume')
            if volume:
                contents['journal_volume'] = volume[0].text.strip()
            issue = journal[0].xpath('descendant::issue')
            if issue:
                contents['journal_issue'] = issue[0].text.strip()

        return contents

    def parse_datacite(self, tree):
        # Parse an DataCite Metadata Schema xml

        return None

    def parse_rdf(self, tree):
        # Parse an rdf xml

        return None

    def make_query(self, q, log, timeout=30):
        br = self.browser
        try:
            raw = br.open_novisit(q, timeout=timeout)
        except HTTPError:
                err = 'The request failed so most probably this DOI doesn\'t exist'
                log.warning(err)
                return None, None

        # Check if all was ok and log the corresponding errors if status is found
        status = raw.info().get('status', None)
        if status is not None:
            status = status[:3]
            if status == '200':
                # Parse the request & return a tree & a content type if all is Ok
                return self.tree_with_content_type(raw)
            elif status == '204':
                err = 'No metadata available for this DOI'
                log.warning(err)
            elif status == '404':
                err = 'This DOI doesn\'t exist'
                log.error(err)
            elif status == '406':
                err = 'None of the requested content types are available from this server'
                log.error(err)
            return None, None

        # Some servers aren't kind enough to send a status so we manage...
        # Assume that if there is no error, we send to the parser
        return self.tree_with_content_type(raw)

    def tree_with_content_type(self, raw):
        # Parse the request & return a tree & a content type
        parser = etree.XMLParser(recover=True, no_network=True)
        return raw.info().dict['content-type'], \
                    etree.fromstring(xml_to_unicode(clean_ascii_chars(raw.read()),
                    strip_encoding_pats=True)[0], parser=parser)
    # }}}

if __name__ == '__main__':
    # To run these test use:
    # calibre-debug -e src/calibre/ebooks/metadata/sources/doi.py
    # set CALIBRE_DEVELOP_FROM=E:\Developpement\calibre\src
    # calibre-debug -e "E:\Developpement\calibre\src\calibre\ebooks\metadata\sources\doi.py"
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
            title_test, authors_test)
    # Tests of different contents for every DOI provider coming
    # from: http://www.doi.org/demos.html
    test_identify_plugin(DOI.name,
        [
            # Extra:
            # (
                # {'identifiers':{'doi':'10.1016/j.electacta.2012.03.132'}},
                # [title_test('Hydrogen peroxide as a sustainable energy carrier: '
                    # 'Electrocatalytic production of hydrogen peroxide and the fuel cell', exact=True),
                    # authors_test(['Shunichi Fukuzumi'])]
            # ),

            # Crossref:
            # - Journal article
            (
                {'identifiers':{'doi':'10.10.1038/nphys1170'}},
                [title_test('Quantum tomography: Measured measurement', exact=True),
                authors_test(['Markus Aspelmeyer'])]
            ),

            # - Book Chapter
            # (
                # {'identifiers':{'doi':'10.1002/0470841559.ch1'}},
                # [title_test('Internetworking LANs and WANs', exact=True),
                # authors_test(['Held, Gilbert'])]
            # ),

            # Datacite:
            # -Sets & Subsets
            # (
                # {'identifiers':{'doi':'10.1594/PANGAEA.726855'}},
                # [title_test('Chemical and mineral compositions of sediments from ODP Site 127-797', exact=True),
                # authors_test(['Irino, T'])]
            # ),

            # Institute of Scientific and Technical Information of China (ISTIC):
            # - Journal article
            # (
                # {'identifiers':{'doi':'10.3866/PKU.WHXB201112303'}},
                # [title_test('Correlation between Bond-Length Change and Vibrational Frequency', exact=False),
                # authors_test(['ZHANG Yu'])]
            # ),

            # - Dissertation:
            # (
                # {'identifiers':{'doi':'10.1002/0470841559.ch1'}},
                # [title_test(u'生物质材料热解失重动力学及其分析方法研究', exact=False),
                # authors_test([u'刘乃安'])]
            # ),

            # Japan Link Center (JaLC):
            # - Journal article
            # (
                # {'identifiers':{'doi':'10.11467/isss2003.7.1_11'}},
                # [title_test(u'大学におけるWebメールとターミナルサービスの研究', exact=False),
                # authors_test([u'竹本 賢太郎'])]
            # ),

            # Multilingual European DOI Registration Agency mEDRA:
            # - Journal article
            # (
                # {'identifiers':{'doi':'10.1430/8105'}},
                # [title_test('L'industria dopo l'euro', exact=True),
                # authors_test(['Prodi, Romano'])]
            # ),

            # - Monograph
            # (
                # {'identifiers':{'doi':'10.1430/8105'}},
                # [title_test('The use of DOI system in eContent value chain', exact=False),
                # authors_test(['Attanasio, Piero'])]
            # ),
    ])

