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
from calibre.ebooks.metadata import check_doi
from calibre.ebooks.metadata.sources.base import Source
from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.icu import lower
from calibre.utils.cleantext import clean_ascii_chars

# An ordered list of the preferred content type for metadata retrieval
_ORDERED_CONTENT_TYPES = ['application/vnd.crossref.unixref+xml',
                    'application/vnd.datacite.datacite+xml', 'application/rdf+xml']

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
            result = self.parse_feed(content_type, xml_tree)
            if result is not None:
                result_queue.put(result)
 
    def parse_feed(self, content_type, tree):
        # Determine the type of content
        if content_type == 'application/vnd.crossref.unixref+xml':
            # Crossref unixref
            mi = self.parse_unixref(tree)
        elif content_type == 'application/vnd.datacite.datacite+xml':
            # DataCite Metadata Schema
            mi = self.parse_datacite(tree)
        elif content_type == 'application/rdf+xml':
            # Simple rdf/xml
            mi = self.parse_rdf(tree)
        else:
            # Unknown content, theoretically impossible
            err = 'Unknown content type sent by the server, weird!'
            log.error(err)
            return None

        return mi

    def parse_unixref(self, tree):
        # Parse an Unixref Crossref xml

        return None

    def parse_datacite(self, tree):
        # Parse an DataCite Metadata Schema xml

        return None

    def parse_rdf(self, tree):
        # Parse an rdf xml

        return None

        # def tostring(x):
            # if x is None:
                # return ''
            # return etree.tostring(x, method='text', encoding=unicode).strip()

        # orig_isbn = identifiers.get('isbn', None)
        # title_tokens = list(self.get_title_tokens(orig_title))
        # author_tokens = list(self.get_author_tokens(orig_authors))
        # results = []

        # def ismatch(title, authors):
            # authors = lower(' '.join(authors))
            # title = lower(title)
            # match = not title_tokens
            # for t in title_tokens:
                # if lower(t) in title:
                    # match = True
                    # break
            # amatch = not author_tokens
            # for a in author_tokens:
                # if lower(a) in authors:
                    # amatch = True
                    # break
            # if not author_tokens: amatch = True
            # return match and amatch

        # bl = feed.find('BookList')
        # if bl is None:
            # err = tostring(feed.find('errormessage'))
            # raise ValueError('ISBNDb query failed:' + err)
        # total_results = int(bl.get('total_results'))
        # shown_results = int(bl.get('shown_results'))
        # for bd in bl.xpath('.//BookData'):
            # isbn = check_isbn(bd.get('isbn', None))
            # isbn13 = check_isbn(bd.get('isbn13', None))
            # if not isbn and not isbn13:
                # continue
            # if orig_isbn and orig_isbn not in {isbn, isbn13}:
                # continue
            # title = tostring(bd.find('Title'))
            # if not title:
                # continue
            # authors = []
            # for au in bd.xpath('.//Authors/Person'):
                # au = tostring(au)
                # if au:
                    # if ',' in au:
                        # ln, _, fn = au.partition(',')
                        # au = fn.strip() + ' ' + ln.strip()
                # authors.append(au)
            # if not authors:
                # continue
            # comments = tostring(bd.find('Summary'))
            # id_ = (title, tuple(authors))
            # if id_ in seen:
                # continue
            # seen.add(id_)
            # if not ismatch(title, authors):
                # continue
            # publisher = tostring(bd.find('PublisherText'))
            # if not publisher: publisher = None
            # if publisher and 'audio' in publisher.lower():
                # continue
            # mi = Metadata(title, authors)
            # mi.isbn = isbn
            # mi.publisher = publisher
            # mi.comments = comments
            # results.append(mi)
        # return total_results, shown_results, results

    def make_query(self, q, log, timeout=30):

        parser = etree.XMLParser(recover=True, no_network=True)
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

        # Datacite isn't kind enough to send a status so we manage...
        # Assume that if there is no error, we send to the parser
        return self.tree_with_content_type(raw)

    def tree_with_content_type(self, raw):
        # Parse the request & return a tree & a content type
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
            # (
                # {'identifiers':{'doi':'10.10.1038/nphys1170'}},
                # [title_test('Quantum tomography: Measured measurement', exact=True),
                # authors_test(['Markus Aspelmeyer'])]
            # ),

            # - Book Chapter
            # (
                # {'identifiers':{'doi':'10.1002/0470841559.ch1'}},
                # [title_test('Internetworking LANs and WANs', exact=True),
                # authors_test(['Held, Gilbert'])]
            # ),

            # Datacite:
            # -Sets & Subsets
            (
                {'identifiers':{'doi':'10.1594/PANGAEA.726855'}},
                [title_test('Chemical and mineral compositions of sediments from ODP Site 127-797', exact=True),
                authors_test(['Irino, T'])]
            ),

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

