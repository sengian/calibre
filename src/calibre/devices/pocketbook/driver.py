#!/usr/bin/env python2
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
# from __future__ import (unicode_literals, division, absolute_import,
                        # print_function)

__license__   = 'GPL v3'
__copyright__ = '2015, Sengian <sengian1@gmail.com>'
__docformat__ = 'restructuredtext en'

'''
Device driver for the PocketBook devices
'''

import re
import sqlite3 as sqlite
# import os, time, re
# from contextlib import closing
# from datetime import date

# from calibre import fsync
# from calibre.devices.mime import mime_type_ext
# from calibre.devices.errors import DeviceError
from calibre.devices.usbms.driver import USBMS, debug_print
# from calibre.devices.usbms.device import USBDevice
from calibre.devices.usbms.books import BookList, CollectionsBookList
from calibre.devices.eb600.driver import EB600
# from calibre.ebooks.metadata import authors_to_sort_string, authors_to_string
# from calibre.constants import islinux

class POCKETBOOK360(EB600):

    # Device info on OS X
    # (8069L, 5768L, 272L, u'', u'', u'1.00')

    name = 'PocketBook 360 Device Interface'

    gui_name = 'PocketBook 360'
    VENDOR_ID   = [0x1f85, 0x525]
    PRODUCT_ID  = [0x1688, 0xa4a5]
    BCD         = [0x110]

    FORMATS = ['epub', 'fb2', 'prc', 'mobi', 'pdf', 'djvu', 'rtf', 'chm', 'txt']

    VENDOR_NAME = ['PHILIPS', '__POCKET', 'POCKETBO']
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = ['MASS_STORGE', 'BOOK_USB_STORAGE',
            'OK_POCKET_611_61', 'OK_POCKET_360+61']

    OSX_MAIN_MEM = OSX_CARD_A_MEM = 'Philips Mass Storge Media'
    OSX_MAIN_MEM_VOL_PAT = re.compile(r'/Pocket')

    @classmethod
    def can_handle(cls, dev, debug=False):
        return dev[-1] == '1.00' and not dev[-2] and not dev[-3]

class POCKETBOOK301(USBMS):

    name           = 'PocketBook 301 Device Interface'
    description    = _('Communicate with the PocketBook 301 reader.')
    author         = 'Kovid Goyal'
    supported_platforms = ['windows', 'osx', 'linux']
    FORMATS = ['epub', 'fb2', 'prc', 'mobi', 'pdf', 'djvu', 'rtf', 'chm', 'txt']

    SUPPORTS_SUB_DIRS = True

    MAIN_MEMORY_VOLUME_LABEL  = 'PocketBook 301 Main Memory'
    STORAGE_CARD_VOLUME_LABEL = 'PocketBook 301 Storage Card'

    VENDOR_ID   = [0x1]
    PRODUCT_ID  = [0x301]
    BCD         = [0x132]

class POCKETBOOK602(USBMS):

    name = 'PocketBook Pro 602/902 Device Interface'
    description    = _('Communicate with the PocketBook 515/602/603/902/903/Pro 912 reader.')
    author         = 'Kovid Goyal'
    supported_platforms = ['windows', 'osx', 'linux']
    FORMATS = ['epub', 'fb2', 'prc', 'mobi', 'pdf', 'djvu', 'rtf', 'chm',
            'doc', 'tcr', 'txt']

    EBOOK_DIR_MAIN = 'books'
    SUPPORTS_SUB_DIRS = True
    SCAN_FROM_ROOT = True

    VENDOR_ID   = [0x0525]
    PRODUCT_ID  = [0xa4a5]
    BCD         = [0x0324, 0x0330]

    VENDOR_NAME = ['', 'LINUX']
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = ['PB602', 'PB603', 'PB902',
            'PB903', 'Pocket912', 'PB', 'FILE-STOR_GADGET']

class POCKETBOOK622(POCKETBOOK602):

    name = 'PocketBook 622 Device Interface'
    description    = _('Communicate with the PocketBook 622 and 623 readers.')
    EBOOK_DIR_MAIN = ''

    VENDOR_ID   = [0x0489]
    PRODUCT_ID  = [0xe107, 0xcff1]
    BCD         = [0x0326]

    VENDOR_NAME = 'LINUX'
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = 'FILE-STOR_GADGET'

class POCKETBOOK360P(POCKETBOOK602):

    name = 'PocketBook 360+ Device Interface'
    description    = _('Communicate with the PocketBook 360+ reader.')
    BCD         = [0x0323]
    EBOOK_DIR_MAIN = ''

    VENDOR_NAME = '__POCKET'
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = 'BOOK_USB_STORAGE'

class POCKETBOOK701(USBMS):

    name = 'PocketBook 701 Device Interface'
    description = _('Communicate with the PocketBook 701')
    author = _('Kovid Goyal')

    supported_platforms = ['windows', 'osx', 'linux']
    FORMATS = ['epub', 'fb2', 'prc', 'mobi', 'pdf', 'djvu', 'rtf', 'chm',
            'doc', 'tcr', 'txt']

    EBOOK_DIR_MAIN = 'books'
    SUPPORTS_SUB_DIRS = True

    VENDOR_ID   = [0x18d1]
    PRODUCT_ID  = [0xa004]
    BCD         = [0x0224]

    VENDOR_NAME = 'ANDROID'
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = '__UMS_COMPOSITE'

    def windows_sort_drives(self, drives):
        if len(drives) < 2:
            return drives
        main = drives.get('main', None)
        carda = drives.get('carda', None)
        if main and carda:
            drives['main'] = carda
            drives['carda'] = main
        return drives

THUMBPATH = 'system/cover_cache' #TBC

# class ImageWrapper(object):
    # def __init__(self, image_path):
        # self.image_path = image_path

class POCKETBOOK(USBMS):
    name           = 'PocketBook Device Interface'
    gui_name       = 'PocketBook Reader'
    description    = _('Communicate with the PocketBook readers')
    author         = 'Sengian'
    version = (1, 0, 0)

    # PocketBook specific
    db_version = 0
    fw_version = 0
    supported_dbversion = 120
    db_path = None
    PB_VERSION_DB='PocketBook'

    supported_platforms = ['windows', 'osx', 'linux']

    # booklist_class = CollectionsBookList
    # book_class = Book

    # List of supported formats (To be completed)
    FORMATS      = ['epub', 'pdf', 'fb2', 'txt', 'pdf', 'html', 'djvu', 'doc', 'docx', 'rtf', 'chm', 'mobi']
    CAN_SET_METADATA = ['title', 'authors', 'collections']

    VENDOR_ID    = [0xfffe]   #: PocketBook Vendor Id
    # PRODUCT_ID   = [0x05c2] #Check Wifi, put generic here
    # BCD          = [0x226]
    DEVICE_NAME = 'PocketBook'

    SUPPORTS_SUB_DIRS = True
    SCAN_FROM_ROOT = True
    MUST_READ_METADATA = True
    THUMBNAIL_HEIGHT = 144 # To be confirmed

    EBOOK_DIR_MAIN   = ''
    MAIN_MEMORY_VOLUME_LABEL = 'PocketBook Reader Main Memory'
    STORAGE_CARD_VOLUME_LABEL = 'PocketBook Reader Storage Card'

    # SUPPORTS_ANNOTATIONS = True
    # CAN_DO_DEVICE_DB_PLUGBOARD = True

    # SUPPORTS_USE_AUTHOR_SORT = True

    EXTRA_CUSTOMIZATION_MESSAGE = [
            _('The PocketBook supports several collections including ')+
                    'Read, Closed, Im_Reading. ' +
            _('Create tags for automatic management'),
            _('Upload separate covers for books') +
            ':::'+_('Normally, the PocketBook readers get the cover image from the'
                ' ebook file itself. With this option, calibre will send a '
                'separate cover image to the reader, useful if you '
                'have modified the cover.') 
    ]
        # _('Comma separated list of metadata fields '
        # 'to turn into collections on the device. Possibilities include: ')+
        # 'series, tags, authors',
        # _('Upload separate cover thumbnails for books') +
        # ':::'+_('Normally, the SONY readers get the cover image from the'
                # ' ebook file itself. With this option, calibre will send a '
                # 'separate cover image to the reader, useful if you are '
                # 'sending DRMed books in which you cannot change the cover.'),
        # _('Refresh separate covers when using automatic management') +
        # ':::' +
        # _('Set this option to have separate book covers uploaded '
          # 'every time you connect your device. Unset this option if '
          # 'you have so many books on the reader that performance is '
          # 'unacceptable.'),

    EXTRA_CUSTOMIZATION_DEFAULT = [
                ', '.join(['series', 'tags']),
                # True,
                False,
                # True,
                # False,
    ]

    OPT_COLLECTIONS    = 0
    OPT_UPLOAD_COVERS  = 1
    # OPT_REFRESH_COVERS = 2
    # OPT_PRESERVE_ASPECT_RATIO = 3
    # OPT_USE_SONY_AUTHORS = 4

    # plugboards = None
    # plugboard_func = None


    def _device_database_path(self):
        # DB path in global, only one path anyway
        self.db_path self.normalize_path(self._main_prefix + 'system/explorer-2/explorer-2.db')

    def _device_firmware(self):
        # Return a dict with all the infos from the reader (only for fw before 5) (TBC)
        self.fw_version = 'Unknown'
        try:
            open(self.normalize_path(self._main_prefix + 'fwinfo.txt')),
                    'rb') as f:
                self.fw_version = f.readline().split(',')[2]
        except:
            debug_print('{0}: Firmware is newer than 4.x or unknown error occured'.format(PB_VERSION_DB))

    def _device_db_version(self, connection=None):
        # Give self.db_version an integer with the db version
        if connection is None:
            with closing(sqlite.connect(self.db_path)
                    ) as connection:

                cursor = connection.cursor()

                cursor.execute('select id from version')
                self.db_version = cursor.fetchone()[0]
        else:
            cursor = connection.cursor()
            cursor.execute('select id from version')
            self.db_version = cursor.fetchone()[0]

        debug_print("{0} - Database Version: {1!s}".format(PB_VERSION_DB, self.dbversion))

    def books(self, oncard=None, end_session=True):
        # Return a list of ebooks on the device
        from calibre.ebooks.metadata.meta import path_to_ext

        dummy_bl = BookList(None, None, None)

        # Return a dummy db if synchronization of books is not done
        if (
                (oncard == 'carda' and not self._card_a_prefix) or
                (oncard and oncard != 'carda')
            ):
            self.report_progress(1.0, _('Getting list of books on device...'))
            return dummy_bl

        prefix = self._card_a_prefix if oncard == 'carda' \
                 else self._main_prefix

        # Determine the firmware version
        self._device_firmware()

        debug_print('Version of driver: ', self.version)
        debug_print('Version of firmware: ', self.fw_version)

        # Implement a custom function on rebuild collections for the BookListCollection class
        self.booklist_class.rebuild_collections = self.rebuild_collections

        # Get the metadata cache
        bl = self.booklist_class(oncard, prefix, self.settings)
        need_sync = self.parse_metadata_cache(bl, prefix, self.METADATA_CACHE)

        # Make a dict cache of paths so the lookup in the loop below is faster.
        bl_cache = {}
        for idx,b in enumerate(bl):
            bl_cache[b.lpath] = idx

        # TODO: Understand and correct the function once needed
        def update_booklist(prefix, path, title, authors, mime, date, ContentType, ImageID, readstatus, MimeType, expired, favouritesindex, accessibility):
            changed = False
            try:
                lpath = path.partition(self.normalize_path(prefix))[2]
                if lpath.startswith(os.sep):
                    lpath = lpath[len(os.sep):]
                lpath = lpath.replace('\\', '/')
                debug_print("LPATH: ", lpath, "  - Title:  " , title)

                playlist_map = {}

                if lpath not in playlist_map:
                    playlist_map[lpath] = []

                if readstatus == 1:
                    playlist_map[lpath].append('Im_Reading')
                elif readstatus == 2:
                    playlist_map[lpath].append('Read')
                elif readstatus == 3:
                    playlist_map[lpath].append('Closed')

                # Related to a bug in the Kobo firmware that leaves an expired row for deleted books
                # this shows an expired Collection so the user can decide to delete the book
                if expired == 3:
                    playlist_map[lpath].append('Expired')
                # A SHORTLIST is supported on the touch but the data field is there on most earlier models
                if favouritesindex == 1:
                    playlist_map[lpath].append('Shortlist')

                # Label Previews
                if accessibility == 6:
                    playlist_map[lpath].append('Preview')
                elif accessibility == 4:
                    playlist_map[lpath].append('Recommendation')

                path = self.normalize_path(path)
                # print "Normalized FileName: " + path

                idx = bl_cache.get(lpath, None)
                if idx is not None:
                    bl_cache[lpath] = None
                    if ImageID is not None:
                        imagename = self.normalize_path(self._main_prefix + '.kobo/images/' + ImageID + ' - NickelBookCover.parsed')
                        if not os.path.exists(imagename):
                            # Try the Touch version if the image does not exist
                            imagename = self.normalize_path(self._main_prefix + '.kobo/images/' + ImageID + ' - N3_LIBRARY_FULL.parsed')

                        # print "Image name Normalized: " + imagename
                        if not os.path.exists(imagename):
                            debug_print("Strange - The image name does not exist - title: ", title)
                        if imagename is not None:
                            bl[idx].thumbnail = ImageWrapper(imagename)
                    if (ContentType != '6' and MimeType != 'Shortcover'):
                        if os.path.exists(self.normalize_path(os.path.join(prefix, lpath))):
                            if self.update_metadata_item(bl[idx]):
                                # print 'update_metadata_item returned true'
                                changed = True
                        else:
                            debug_print("    Strange:  The file: ", prefix, lpath, " does mot exist!")
                    if lpath in playlist_map and \
                        playlist_map[lpath] not in bl[idx].device_collections:
                            bl[idx].device_collections = playlist_map.get(lpath,[])
                else:
                    if ContentType == '6' and MimeType == 'Shortcover':
                        book =  Book(prefix, lpath, title, authors, mime, date, ContentType, ImageID, size=1048576)
                    else:
                        try:
                            if os.path.exists(self.normalize_path(os.path.join(prefix, lpath))):
                                book = self.book_from_path(prefix, lpath, title, authors, mime, date, ContentType, ImageID)
                            else:
                                debug_print("    Strange:  The file: ", prefix, lpath, " does mot exist!")
                                title = "FILE MISSING: " + title
                                book =  Book(prefix, lpath, title, authors, mime, date, ContentType, ImageID, size=1048576)

                        except:
                            debug_print("prefix: ", prefix, "lpath: ", lpath, "title: ", title, "authors: ", authors,
                                        "mime: ", mime, "date: ", date, "ContentType: ", ContentType, "ImageID: ", ImageID)
                            raise

                    # print 'Update booklist'
                    book.device_collections = playlist_map.get(lpath,[])  # if lpath in playlist_map else []

                    if bl.add_book(book, replace_metadata=False):
                        changed = True
            except:  # Probably a path encoding error
                import traceback
                traceback.print_exc()
            return changed

        with closing(sqlite.connect(self.db_path)) as connection:

            # Return bytestrings if the content cannot the decoded as unicode
            # instead of erroring out
            connection.text_factory = lambda x: unicode(x, "utf-8", "ignore")

            self._device_db_version(connection=connection)

            opts = self.settings()
            default_query='''
            SELECT 
                 b.storageid AS storageid,
                 f.name AS foldername,
                 b.id AS id,
                 b.folderid AS folderid,
                 b.filename AS filename, 
                 b.name AS name,
                 b.ext AS ext,
                 b.title AS title,
                 b.author AS author,
                 b.firstauthor AS firstauthor,
                 b.series AS series,
                 b.numinseries AS numinseries,
                 b.size AS size,
                 "1" AS updated,
                 null AS opentime,
                 "1368618807" AS creationtime
             FROM
             books_impl b JOIN folders f ON b.folderid = f.id LEFT OUTER JOIN books_settings bs ON b.id = bs.bookidselect'''
            if self.dbversion >= 14:
                query='''
                SELECT 
                     b.storageid AS storageid,
                     f.name AS foldername,
                     b.id AS id,
                     b.folderid AS folderid,
                     b.filename AS filename, 
                     b.name AS name,
                     b.ext AS ext,
                     b.title AS title,
                     b.author AS author,
                     b.firstauthor AS firstauthor,
                     b.series AS series,
                     b.numinseries AS numinseries,
                     b.size AS size,
                     b.updated AS updated,
                     bs.opentime AS opentime,
                     b.creationtime AS creationtime
                 FROM
                 books_impl b JOIN folders f ON b.folderid = f.id LEFT OUTER JOIN books_settings bs ON b.id = bs.bookidselect'''
            else:
                query= default_query

            try:
                cursor.execute(query)
            except Exception as e:
                err = str(e)
                #Non killing errors
                if not ('opentime' in err or 'creationtime' in err or
                        'updated' in err):
                    raise
                cursor.execute(default_query)

            changed = False
            for i, row in enumerate(cursor):
            #  self.report_progress((i+1) / float(numrows), _('Getting list of books on device...'))
                path = self.path_from_contentid(row[3], row[5], row[4], oncard)
                mime = mime_type_ext(path_to_ext(path)) if path.find('kepub') == -1 else 'application/epub+zip'
                # debug_print("mime:", mime)

                if oncard != 'carda' and not row[3].startswith("file:///mnt/sd/"):
                    changed = update_booklist(self._main_prefix, path, row[0], row[1], mime, row[2], row[5], row[6], row[7], row[4], row[8], row[9], row[10])
                    # print "shortbook: " + path
                elif oncard == 'carda' and row[3].startswith("file:///mnt/sd/"):
                    changed = update_booklist(self._card_a_prefix, path, row[0], row[1], mime, row[2], row[5], row[6], row[7], row[4], row[8], row[9], row[10])

                if changed:
                    need_sync = True

            cursor.close()

        # Remove books that are no longer in the filesystem. Cache contains
        # indices into the booklist if book not in filesystem, None otherwise
        # Do the operation in reverse order so indices remain valid
        for idx in sorted(bl_cache.itervalues(), reverse=True):
            if idx is not None:
                need_sync = True
                del bl[idx]

        # print "count found in cache: %d, count of files in metadata: %d, need_sync: %s" % \
        #      (len(bl_cache), len(bl), need_sync)
        if need_sync:  # self.count_found_in_bl != len(bl) or need_sync:
            if oncard == 'cardb':
                self.sync_booklists((None, None, bl))
            elif oncard == 'carda':
                self.sync_booklists((None, bl, None))
            else:
                self.sync_booklists((bl, None, None))

        self.report_progress(1.0, _('Getting list of books on device...'))
        return bl

    def path_from_contentid(self, filename, foldername, oncard):
        # Return the path of a book from database information and calibre mounting infos

        if oncard == 'carda':
            foldername = re.sub("/mnt/ext\d+", self._card_a_prefix, foldername)
            # debug_print("SD Card path:", path)
        else:
            foldername = re.sub("/mnt/ext\d+", self._main_prefix, foldername)
            # debug_print("Internal memory path:", path)

        return foldername + '/' + filename

class POCKETBOOK626(POCKETBOOK):

    name  = 'PocketBook Touch Lux 2'
    description    = _('Communicate with the PocketBook Touch Lux 2 reader')

    # List of supported formats
    FORMATS     = ['epub', 'pdf', 'fb2', 'txt', 'pdf', 'html', 'djvu', 'doc',       'docx', 'rtf', 'chm'] # To be removed or integrated?

    # PRODUCT_ID  = [0x0001]
    # BCD         = [0x0230]
    DEVICE_NAME = 'PocketBook 626'

    VENDOR_NAME = ['USB_2.0']
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = ['USB_FLASH_DRIVER']

    MAIN_MEMORY_VOLUME_LABEL = 'PocketBook Touch Lux 2 Main Memory'
    STORAGE_CARD_VOLUME_LABEL = 'PocketBook Touch Lux 2 Storage Card'
