# -*- coding: utf-8 -*-
import os
import re
import six
import shutil
import urllib
import zipfile
import logging
import StringIO
import urlparse
import ebooklib
from lxml import etree

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from booki.editor import models

from ..base import BaseConverter

try:
    import Image
except ImportError:
    from PIL import Image

logger = logging.getLogger("booktype.convert.xml")

FONTS_DIR = "Fonts"
IMAGES_DIR = "Images"


class XMLConverter(BaseConverter):
    name = 'xml'
    verbose_name = _('XML')
    support_section_settings = False

    def __init__(self, *args, **kwargs):
        super(XMLConverter, self).__init__(*args, **kwargs)

        self._book = None
        self._original_book = None
        self._output_path = None
        self._sandbox_path_images = os.path.join(self.sandbox_path, IMAGES_DIR)
        self._sandbox_path_fonts = os.path.join(self.sandbox_path, FONTS_DIR)

    def convert(self, original_book, output_path):
        logger.debug('[XML] XMLConverter.convert')

        self._book = models.Book.objects.get(url_title=self._config['project_id'])
        self._ooutput_path = output_path
        self._original_book = original_book
        self.output_file = zipfile.ZipFile(output_path, 'w')
        self._copy_static()

        xml_content = self._create_xml()
        self.output_file.writestr('document.xml', xml_content)
        self.output_file.close()

        fd = open(os.path.join(self.sandbox_path, 'document.xml'), 'w')
        fd.write(xml_content)
        fd.close()
        # self._clean_up()

        return {"size": os.path.getsize(output_path)}

    def _clean_up(self):
        shutil.rmtree(self._sandbox_path_images)
        shutil.rmtree(self._sandbox_path_fonts)

    def _copy_static(self):
        self._copy_images()
        self._copy_fonts()

    def _copy_images(self):
        # to sandbox
        shutil.copytree(
            os.path.join(settings.DATA_ROOT, 'books', self._book.url_title, self._book.version.get_version()),
            self._sandbox_path_images
        )
        # to zipfile
        for file_name in os.listdir(self._sandbox_path_images):
            try:
                with open(os.path.join(self._sandbox_path_images, file_name), 'r') as img:
                    self.output_file.writestr('{}/{}'.format(IMAGES_DIR, file_name), img.read())
            except IOError:
                logger.exception("xml. Failed to open image for writing.")

    def _copy_fonts(self):
        # to sandbox
        shutil.copytree(
            os.path.join(settings.BOOKTYPE_ROOT, 'themes', self._config['theme']['id'], 'static', 'fonts'),
            self._sandbox_path_fonts
        )
        # to zipfile
        for file_name in os.listdir(self._sandbox_path_fonts):
            try:
                with open(os.path.join(self._sandbox_path_fonts, file_name), 'r') as img:
                    self.output_file.writestr('{}/{}'.format(FONTS_DIR, file_name), img.read())
            except IOError:
                logger.exception("xml. Failed to open fonts for writing.")

    def _create_xml(self):
        root = etree.Element("document")

        for item in self._original_book.get_items():
            item_type = item.get_type()
            file_name = os.path.basename(item.file_name)

            if item_type == ebooklib.ITEM_DOCUMENT:
                if isinstance(item, ebooklib.epub.EpubNav):
                    pass
                elif not isinstance(item, ebooklib.epub.EpubNcx):
                    root.append(
                        self._convert_chapter_to_xml(item.get_content())
                    )

        xml_content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return xml_content

    def _convert_chapter_to_xml(self, content):
        content = content.replace('&nbsp;', '##@@##')

        root = ebooklib.utils.parse_html_string(content)
        body = root.find("body")

        # Remove empty tags
        for name in [".//p", ".//i", ".//b", ".//span", ".//ul", ".//h1", ".//h2", ".//h3", ".//sup"]:
            self._remove_empty_tags(body.xpath(name))

        # drop tables
        for _table in body.xpath('.//table'):
            _table.drop_tree()

        # rawify images
        self._rawify_images(body)

        # TODO
        # What is with this?
        for h1 in body.xpath('.//h1'):
            h1.tag = 'B1Heading'
            self._remove_attributes_for_element(h1)
            self._remove_newline(h1)

        for s1 in body.xpath(".//span[@class='text-subtitle']"):
            s1.tag = 'B2ReferenceTitle'
            self._remove_attributes_for_element(s1)
            self._remove_newline(s1)
            if self._book.language == 'arabic':
                self._check_for_arabic(s1)

        for h2 in body.xpath('.//h2'):
            h2.tag = 'B6HeadingText'
            self._remove_attributes_for_element(h2)
            self._remove_newline(h2)

        for p in body.xpath(".//p[@class='text-p']"):
            p.tag = 'B5BodyText'
            self._remove_attributes_for_element(p)
            self._remove_newline(p)
            if self._book.language == 'arabic':
                self._check_for_arabic(p)

        for quote in body.xpath(".//p[@class='text-inline-quote']"):
            quote.tag = 'B7QuoteBold'
            self._remove_attributes_for_element(quote)

            if quote.text and quote.text[0] in [u"\u201e", u"\u201d", u"\u201a", u"\u2019", u'"', u'“', u'„']:
                quote.text = u' ' + quote.text

            if self._book.language == 'arabic':
                self._check_for_arabic(quote)

        for quote in body.xpath(".//div[@class='text-quote']"):
            quote.tag = 'ForewordQuote2'
            imprint_pos = body.index(quote)

            self._remove_attributes_for_element(quote)

            # quote.tag = 'Imprint'
            # remove_attributes_for_element(imprint)

            for p in quote.xpath(".//p"):
                p.tag = 'B3Quote'

                self._remove_attributes_for_element(p)
                self._remove_newline(p)

                if p.text and p.text[0] in [u"\u201e", u"\u201d", u"\u201a", u"\u2019", u'"', u'“', u'„']:
                    p.text = u' ' + p.text

                if self._book.language == 'arabic':
                    self._check_for_arabic(p)

            for p in quote.xpath(".//div"):
                p.tag = 'B4QuoteReference'
                self._remove_attributes_for_element(p)
                self._remove_newline(p)

                if self._book.language == 'arabic':
                    self._check_for_arabic(p)

        for sup in body.xpath('.//sup'):
            text = sup.text or ''

            for a in sup.xpath('.//a'):
                text += a.text
                if a.tail is not None:
                    text += a.tail
                sup.remove(a)
            sup.text = text

        for ol in body.xpath(".//ol[@class='endnotes']"):
            la = etree.Element('lineaboveC8endNote')
            ol.insert(0, la)

            ol.tag = 'C8EndNotes'
            self._remove_attributes_for_element(ol)

            def _eat_nbsp(text):
                text = text.rstrip()
                if text.endswith('##@@##'):
                    return _eat_nbsp(text[:-6])

                return text

            def _eat_behind(text):
                text = text.lstrip()
                if text.startswith(';'):
                    return _eat_behind(text[1:])

                return text

            #        for p in ol.xpath(".//p"):
            for p in ol.xpath(".//li"):
                p.tag = 'C8EndNote'
                self._remove_attributes_for_element(p)

                etree.strip_tags(p, "p")

                _links = list(p.xpath(".//a"))
                max_links = len(_links)

                _prev = None
                for _x in p.iter():
                    if _x.tag == 'a':
                        if _prev is not None:
                            if _prev.tail:
                                _tail = _prev.tail[:].rstrip()
                                _tail = _eat_nbsp(_tail)

                                if self._book.language == 'arabic':
                                    c = re.compile("(\([\s\nA-Z\/\d]*\))", re.L)
                                    _m = c.search(_tail)

                                    if _m:
                                        _tail = c.sub(r'@!@!\1#!#!', _tail)

                                if _tail.endswith(','):
                                    _tail = _tail[:-1] + ' '
                                    _prev.tail = _tail
                                else:
                                    _tail = _tail + ' '
                                    _prev.tail = _tail
                            elif _prev.text:
                                _text = _prev.text[:].rstrip()
                                _text = _eat_nbsp(_text)

                                if self._book.language == 'arabic':
                                    c = re.compile("(\([\s\nA-Z\/\d]*\))", re.L)
                                    _m = c.search(_text)

                                    if _m:
                                        _text = c.sub(r'@!@!\1#!#!', _text)

                                if _text.endswith(','):
                                    _text = _text[:-1] + ' '
                                    _prev.text = _text
                                else:
                                    _text = _text + ' '
                                    _prev.text = _text
                    else:
                        if self._book.language == 'arabic':
                            if _x.tail and '@!@!' not in _x.tail:
                                c = re.compile("(\([\s\nA-Z\/\d]*\))", re.L)
                                _m = c.search(_x.tail)

                                if _m:
                                    _x.tail = c.sub(r'@!@!\1#!#!', _x.tail)

                            if _x.text and '@!@!' not in _x.text:
                                c = re.compile("(\([\s\nA-Z\/\d]*\))", re.L)
                                _m = c.search(_x.text)

                                if _m:
                                    _x.text = c.sub(r'@!@!\1#!#!', _x.text)

                    _prev = _x

                for _n, _a in enumerate(_links):
                    if _n + 1 != max_links:
                        _tail = _a.tail or ''
                        _tail = _eat_behind(_tail)
                        _a.tail = u"$$##$$" + _tail
                    if _a.text:
                        if _a.text.startswith("http://"):
                            _a.text = _a.text[7:]

                if p.text is None:
                    if len(list(p)) == 0:
                        p.drop_tree()
                else:
                    text = p.text_content().replace("\n", "").strip()
                    self._remove_newline(p)

                    if text == u"":
                        p.drop_tree()

        for p in body.xpath(".//p"):
            p.tag = 'B5BodyText'
            self._remove_attributes_for_element(p)
            self._remove_newline(p)
            if self._book.language == 'arabic':
                self._check_for_arabic(p)

                self._handle_bold_and_italic_all(body)

        previous_tag = ''
        for elem in body.iter():
            if previous_tag in ['B6HeadingText', 'B1Heading', 'B4QuoteReference', 'B7QuoteBold', 'B3Quote']:
                if elem.tag == 'B5BodyText':
                    elem.tag = 'B5BodyTextFirstPara'

            previous_tag = elem.tag

        body = self._transform_document(body)

        return body

    def _remove_empty_tags(self, elements):
        "Remove all empty tags for this list of elements"

        def _strip(t):
            t = t.replace('##@@##', '')
            return t.strip()

        for elem in elements:
            if elem.text is None:
                # TODO
                # Shouldn't this be drop_tree ?!?!
                # Why at some point we wanted tail to be empty?!
                #            if (elem.tail is None or _strip(elem.tail) == '') and len(list(elem)) == 0:
                if len(list(elem)) == 0:
                    elem.drop_tree()
                # elem.getparent().remove(elem)
            else:
                # Also, why should tail be empty?
                if _strip(elem.text) == u'' and len(list(elem)) == 0:
                    if elem.tail is None or (elem.tail and _strip(elem.tail) == u''):
                        # Use drop_tree() instead of parent.remove(elem)
                        elem.drop_tree()
                    else:
                        if len(elem.text) > 0:
                            elem.tail = elem.text + elem.tail
                            elem.drop_tree()

    def _remove_attributes(self, elements):
        "Remove all attributes for this list of elements."

        for elem in elements:
            self._remove_attributes_for_element(elem)

    def _remove_attributes_for_element(self, elem):
        "Remove all attributes for this element."

        for key in six.iterkeys(elem.attrib):
            del elem.attrib[key]

    def _remove_newline(self, el):
        "Remove newlines from this element text."

        # Remove text from the element
        for elem in el.iter():
            if elem.text is not None:
                if 'Bold' not in el.tag and 'Italic' not in el.tag:
                    elem.text = elem.text.replace("\n", "").lstrip()
                    elem.text = re.sub("\s\s+", " ", elem.text)

            # Remove tail text after the element
            if elem.tail is not None:
                elem.tail = elem.tail.replace("\n", "")
                elem.tail = re.sub("\s\s+", " ", elem.tail)

    def _handle_bold_and_italic(self, body, tag_name):
        for elem in body.xpath('.//{}'.format(tag_name)):
            for ea in elem.xpath('.//b'):
                ea.tag = '{}Bold'.format(tag_name)

            for ea in elem.xpath('.//i'):
                ea.tag = '{}Italic'.format(tag_name)

    def _handle_bold_and_italic_all(self, body):
        self._handle_bold_and_italic(body, 'A2BodyText')
        self._handle_bold_and_italic(body, 'A3SmallText')
        self._handle_bold_and_italic(body, 'A4ImprintText')
        self._handle_bold_and_italic(body, 'B5BodyText')
        self._handle_bold_and_italic(body, 'C6BodyText')
        self._handle_bold_and_italic(body, 'C8EndNote')
        self._handle_bold_and_italic(body, 'C4IntroText')

    def _replace(self, m):
        _s = m.group(0).strip()

        c = re.compile("[\d\.\,]+")
        _m = c.match(_s)

        if _m:
            return m.group(0)

        return r'@!@!{}#!#!'.format(m.group(0))

    def _check_for_arabic(self, el):
        for elem in el.iter():
            if elem.text:
                c = re.compile("([\(\)a-zA-Z\d\s\-\/\:\@\,\.]{4,})", re.L)
                _m = c.search(elem.text)
                if _m:
                    elem.text = c.sub(self._replace, elem.text)

            if elem.tail:
                c = re.compile("([\(\)a-zA-Z\d\s\-\/\:\@\,\.]{4,})", re.L)
                _m = c.search(elem.tail)
                if _m:
                    elem.tail = c.sub(self._replace, elem.tail)

    def _transform_document(self, body):
        "Remove common things from the document at the end."

        # Remove these tags
        etree.strip_tags(body, "span")
        etree.strip_tags(body, "a")
        etree.strip_tags(body, "br")

        # Remove attributes on these elements
        for name in [".//i", ".//b", ".//span", ".//p", ".//h1", ".//h2", ".//h3", ".//h4", ".//ol", ".//ul", ".//li"]:
            self._remove_attributes(body.xpath(name))

        # Remove empty tags
        for name in [".//p", ".//i", ".//b", ".//span", ".//ul", ".//h1", ".//h2", ".//h3", ".//sup"]:
            self._remove_empty_tags(body.xpath(name))

        body.tag = 'content'

        return body

    def _rawify_images(self, body):
        for elem in body.iter('img'):
            div_image = elem.getparent()
            div_group_img = div_image.getparent()

            src = elem.get('src')
            self._remove_attributes_for_element(elem)
            elem.set('src', os.path.join(IMAGES_DIR, src.rsplit('/')[-1]))
            div_group_img.addnext(elem)

            caption_text = None

            # find old captions using p.caption_small
            for p_caption in div_group_img.xpath('p[contains(@class,"caption_small")]'):
                caption_text = p_caption.text

            # find caption
            for div_caption in div_group_img.xpath('div[contains(@class,"caption_small")]'):
                caption_text = div_caption.text

            if caption_text:
                caption = etree.Element("Caption")
                caption.text = caption_text
                elem.addnext(caption)

            div_group_img.drop_tree()
