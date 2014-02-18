#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2014, sengian <sengian1 at gmail.com>'
__docformat__ = 'restructuredtext en'

from urllib import quote as url_quote
from lxml import etree

from calibre.ebooks.chardet import xml_to_unicode
from calibre.ebooks.metadata import check_doi
from calibre.ebooks.metadata.sources.base import Source
from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.icu import lower
from calibre.utils.cleantext import clean_ascii_chars


class DOI(Source):

    name = 'DOI'
    author = 'Sengian'
    description = _('Downloads metadata from doi.org')

    capabilities = frozenset(['identify'])
    touched_fields = frozenset(['title', 'authors', 'identifier:doi'
        'identifier:url', 'pubdate', 'languages', 'publisher'])
    supports_gzip_transfer_encoding = True
    # Shortcut, since we have no cached cover URLS
    cached_cover_url_is_reliable = False

    # An ordered list of the preferred content type for metadata retrieval
    ordered_content_types = ['application/vnd.crossref.unixref+xml',
                    'application/vnd.datacite.datacite+xml', 'application/rdf+xml']


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
            xml_tree = self.make_query(query, log, timeout=timeout)
        except:
            err = 'Failed to make query to doi.org, aborting.'
            log.exception(err)
            return err

        if xml_tree is not None and not abort.is_set():
            # Parse the result and put it in the queue
            # log.error(etree.tostring(xml_tree, pretty_print=True, with_tail=True, method='xml'))
            result = self.parse_feed(xml_tree)
            result_queue.put(result)

    def parse_feed(self, feed):

        def tostring(x):
            if x is None:
                return ''
            return etree.tostring(x, method='text', encoding=unicode).strip()

        orig_isbn = identifiers.get('isbn', None)
        title_tokens = list(self.get_title_tokens(orig_title))
        author_tokens = list(self.get_author_tokens(orig_authors))
        results = []

        def ismatch(title, authors):
            authors = lower(' '.join(authors))
            title = lower(title)
            match = not title_tokens
            for t in title_tokens:
                if lower(t) in title:
                    match = True
                    break
            amatch = not author_tokens
            for a in author_tokens:
                if lower(a) in authors:
                    amatch = True
                    break
            if not author_tokens: amatch = True
            return match and amatch

        bl = feed.find('BookList')
        if bl is None:
            err = tostring(feed.find('errormessage'))
            raise ValueError('ISBNDb query failed:' + err)
        total_results = int(bl.get('total_results'))
        shown_results = int(bl.get('shown_results'))
        for bd in bl.xpath('.//BookData'):
            isbn = check_isbn(bd.get('isbn', None))
            isbn13 = check_isbn(bd.get('isbn13', None))
            if not isbn and not isbn13:
                continue
            if orig_isbn and orig_isbn not in {isbn, isbn13}:
                continue
            title = tostring(bd.find('Title'))
            if not title:
                continue
            authors = []
            for au in bd.xpath('.//Authors/Person'):
                au = tostring(au)
                if au:
                    if ',' in au:
                        ln, _, fn = au.partition(',')
                        au = fn.strip() + ' ' + ln.strip()
                authors.append(au)
            if not authors:
                continue
            comments = tostring(bd.find('Summary'))
            id_ = (title, tuple(authors))
            if id_ in seen:
                continue
            seen.add(id_)
            if not ismatch(title, authors):
                continue
            publisher = tostring(bd.find('PublisherText'))
            if not publisher: publisher = None
            if publisher and 'audio' in publisher.lower():
                continue
            mi = Metadata(title, authors)
            mi.isbn = isbn
            mi.publisher = publisher
            mi.comments = comments
            results.append(mi)
        return total_results, shown_results, results

    def make_query(self, q, log, timeout=30):

        parser = etree.XMLParser(recover=True, no_network=True)
        br = self.browser
        # Add extra headers to specify what metadata format we want
        br.addheaders.append(('accept', ', '.join(self.ordered_content_types)))
        raw = br.open_novisit(q, timeout=timeout)

        # Check if all was ok and log the corresponding errors
        status = raw.info().dict['status'].split(' ')[0]
        if status == '200':
            # Parse the request & return a tree if all is Ok
            return etree.fromstring(xml_to_unicode(clean_ascii_chars(raw.read()),
                strip_encoding_pats=True)[0], parser=parser)
        elif status == '204':
            err = 'No metadata available for this DOI'
            log.warning(err)
        elif status == '404':
            err = 'This DOI doesn\'t exist'
            log.error(err)
        elif status == '406':
            err = 'None of the requested content types are available from this server'
            log.error(err)

        return None
    # }}}

if __name__ == '__main__':
    # To run these test use:
    # calibre-debug -e src/calibre/ebooks/metadata/sources/doi.py
    from calibre.ebooks.metadata.sources.test import (test_identify_plugin,
            title_test, authors_test)
    test_identify_plugin(DOI.name,
        [
            # (
                # {'identifiers':{'doi':'10.1016/j.electacta.2012.03.132'}},
                # [title_test('Hydrogen peroxide as a sustainable energy carrier: '
                    # 'Electrocatalytic production of hydrogen peroxide and the fuel cell', exact=True),
                    # authors_test(['Shunichi Fukuzumi'])]
            # ),

            (
                {'identifiers':{'doi':'10.1039/c3gc40811f'}},
                [title_test('Direct synthesis', exact=False)]
            ),
    ])

