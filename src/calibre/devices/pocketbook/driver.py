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

THUMBPATH = 'system/cover_chache' #TBC

# class ImageWrapper(object):
    # def __init__(self, image_path):
        # self.image_path = image_path

class POCKETBOOK(USBMS):
    name           = 'PocketBook Device Interface'
    gui_name       = 'PocketBook Reader'
    description    = _('Communicate with the PocketBook readers')
    author         = 'Sengian'
    version = (1, 0, 0)

    dbversion = 0
    fwversion = 0
    supported_dbversion = 120

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

    # EXTRA_CUSTOMIZATION_MESSAGE = [
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
        # _('Preserve cover aspect ratio when building thumbnails') +
        # ':::' +
        # _('Set this option if you want the cover thumbnails to have '
          # 'the same aspect ratio (width to height) as the cover. '
          # 'Unset it if you want the thumbnail to be the maximum size, '
          # 'ignoring aspect ratio.'),
        # _('Use SONY Author Format (First Author Only)') +
        # ':::' +
        # _('Set this option if you want the author on the Sony to '
          # 'appear the same way the T1 sets it. This means it will '
          # 'only show the first author for books with multiple authors. '
          # 'Leave this disabled if you use Metadata Plugboards.')
    # ]
    # EXTRA_CUSTOMIZATION_DEFAULT = [
                # ', '.join(['series', 'tags']),
                # True,
                # False,
                # True,
                # False,
    # ]

    # OPT_COLLECTIONS    = 0
    # OPT_UPLOAD_COVERS  = 1
    # OPT_REFRESH_COVERS = 2
    # OPT_PRESERVE_ASPECT_RATIO = 3
    # OPT_USE_SONY_AUTHORS = 4

    # plugboards = None
    # plugboard_func = None

    def _device_database_path(self):
        return self.normalize_path(self._main_prefix + 'system/explorer-2/explorer-2.db')

    def _device_firmware(self):
        # Return a dict with all the infos from the reader (TBC)
        fw_path = self.normalize_path(self._main_prefix + 'fwinfo.txt')
        return ''

    def _device_db_version(self):
        # Return an integer with the db version
        return self.normalize_path(self._main_prefix + 'system/explorer-2/explorer-2.db')
        debug_print('Pocketbook: ')

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
