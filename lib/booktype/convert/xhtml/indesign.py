# -*- coding: utf-8 -*-

import six
import re
import sets

from lxml import etree, html


def parse_html_string(s):
    "Parse HTML document and return lxml node tree."

    utf8_parser = html.HTMLParser(encoding='utf-8')
    html_tree = html.document_fromstring(s , parser=utf8_parser)

    return html_tree


def remove_attributes_for_element(elem):
    "Remove all attributes for this element."

    for key in six.iterkeys(elem.attrib):
        del elem.attrib[key]


def remove_attributes(elements):
    "Remove all attributes for this list of elements."

    for elem in elements:
        remove_attributes_for_element(elem)


def remove_empty_tags(elements):
    "Remove all empty tags for this list of elements"

    # TODO
    # - What to do with elem.tail ????

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
            #elem.getparent().remove(elem)
        else:
            # Also, why should tail be empty?
            if _strip(elem.text) == u'' and len(list(elem)) == 0:
                if elem.tail is None or (elem.tail and _strip(elem.tail) == u''):
                    # Use drop_tree() instead of parent.remove(elem)
                    elem.drop_tree()
                else:
                    if len(elem.text) > 0:
                        elem.tail = elem.text +  elem.tail
                        elem.drop_tree()


def remove_newline(el):
    "Remove newlines from this element text."

    import re

    # Remove text from the element
    for elem in el.iter():
        if elem.text is not None:
            if 'Bold' not in el.tag and 'Italic' not in el.tag:
                elem.text = elem.text.replace("\n", "").lstrip()
                elem.text = re.sub("\s\s+", " ", elem.text)

        # Remove tail text after the element
        if elem.tail is not None:
#            elem.tail = elem.tail.replace("\n", "").lstrip()
            elem.tail = elem.tail.replace("\n", "")

            elem.tail = re.sub("\s\s+", " ", elem.tail)


def _remove_newline(elem):
    "Remove newlines from this element text."

    import re

    # Remove text from the element
    if elem.text is not None:
        elem.text = elem.text.replace("\n", "").lstrip()
        elem.text = re.sub("\s\s+", " ", elem.text)

    # Remove tail text after the element
    if elem.tail is not None:
        elem.tail = elem.tail.replace("\n", "").lstrip()
        elem.tail = re.sub("\s\s+", " ", elem.tail)


def handle_facts(facts):
    "Handle Country facts block"

    if len(facts) == 0: return

    remove_attributes(facts)

    element = facts[0]

    for idx, el in enumerate(element.xpath('.//div')):
        if idx == 0:
            el.tag = 'C3FactCountry2'
        else:
            el.tag = 'C2FactCountry1'
        remove_newline(el)

    element.tag = 'facts'

    etree.SubElement(element, 'lineBelowFacts')


def handle_intro(facts):
    "Handle Country Introduction block."

    if len(facts) == 0: return

    remove_attributes(facts)

    intro = etree.Element("introduction")

    for elem in facts:
        intro.append(etree.fromstring(etree.tostring(elem)))

    return intro


def handle_bold_and_italic(body, tag_name):
    for elem in body.xpath('.//{}'.format(tag_name)):
        for ea in elem.xpath('.//b'):
            ea.tag = '{}Bold'.format(tag_name)

        for ea in elem.xpath('.//i'):
            ea.tag = '{}Italic'.format(tag_name)


def handle_bold_and_italic_all(body):
    handle_bold_and_italic(body, 'A2BodyText')
    handle_bold_and_italic(body, 'A3SmallText')
    handle_bold_and_italic(body, 'A4ImprintText')
    handle_bold_and_italic(body, 'B5BodyText')
    handle_bold_and_italic(body, 'C6BodyText')
    handle_bold_and_italic(body, 'C8EndNote')
    handle_bold_and_italic(body, 'C4IntroText')
#    handle_bold_and_italic(body, 'B6HeadingText')

## TRANSFORM DOCUMENTS

def transform_document_before(body):
    # Remove empty tags
    for name in [".//p", ".//i", ".//b", ".//span", ".//ul", ".//h1", ".//h2", ".//h3", ".//sup"]:
        remove_empty_tags(body.xpath(name))

    for _table in body.xpath('.//table'):
        _table.drop_tree()


def transform_document(body):
    "Remove common things from the document at the end."

    # Remove these tags
    etree.strip_tags(body, "span")
    etree.strip_tags(body, "a")
    etree.strip_tags(body, "br")

    # Remove attributes on these elements
    for name in [".//i", ".//b", ".//span", ".//p", ".//h1", ".//h2", ".//h3", ".//h4", ".//ol", ".//ul", ".//li"]:
        remove_attributes(body.xpath(name))

    # Remove empty tags
    for name in [".//p", ".//i", ".//b", ".//span", ".//ul", ".//h1", ".//h2", ".//h3", ".//sup"]:
        remove_empty_tags(body.xpath(name))

    body.tag = 'content'

    return body


################################################################################

def _replace(m):
    _s = m.group(0).strip()

    c = re.compile("[\d\.\,]+")
    _m = c.match(_s)

    if _m:
        return m.group(0)

    return r'@!@!{}#!#!'.format(m.group(0))

def _check_for_arabic(el):
    for elem in el.iter():
        if elem.text:
            c = re.compile("([\(\)a-zA-Z\d\s\-\/\:\@\,\.]{4,})", re.L)
            _m = c.search(elem.text)
            if _m:
                elem.text = c.sub(_replace, elem.text)

        if elem.tail:
            c = re.compile("([\(\)a-zA-Z\d\s\-\/\:\@\,\.]{4,})", re.L)
            _m = c.search(elem.tail)
            if _m:
                elem.tail = c.sub(_replace, elem.tail)


def export_first(content, language):
    "Export first page."

    root = parse_html_string(content)
    body = root.find("body")

    transform_document_before(body)

    # TODO
    # What is with this?
    for h1 in body.xpath('.//h1'):
        h1.tag = 'A1Heading'
        remove_attributes_for_element(h1)
        remove_newline(h1)

    for h2 in body.xpath('.//h2'):
        h2.tag = 'A8TitleAbbreviations'
        remove_attributes_for_element(h2)
        remove_newline(h2)


    for p in body.xpath(".//p[@class='intro-p']"):
        p.tag = 'A2BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)


    for p in body.xpath(".//p[@class='intro-small']"):
        p.tag = 'A3SmallText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)


    for imprint in body.xpath(".//div[@class='intro-imprint']"):
        imprint_pos = body.index(imprint)

        imprint.tag = 'Imprint'
        remove_attributes_for_element(imprint)

        for p in imprint.xpath(".//p"):
            p.tag = 'A4ImprintText'
            remove_attributes_for_element(p)
            remove_newline(p)
            if language == 'arabic':
                _check_for_arabic(p)

    for p in body.xpath(".//p"):
        p.tag = 'A2BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)

    handle_bold_and_italic_all(body)

    previous_tag = ''
    for elem in body.iter():
        if previous_tag == 'A1Heading':
            if elem.tag == 'A2BodyText':
                elem.tag = 'A2BodyTextFirstPara'

        previous_tag = elem.tag


    previous_tag = ''
    for elem in body.iter():
        if previous_tag in ['Imprint']:
            if elem.tag == 'A4ImprintText':
                elem.tag = 'A4ImprintTextFirstPara'

        previous_tag = elem.tag

    body = transform_document(body)

    return body


def export_abbreviation(content, language):
    "Export abbreviation page."

    root = parse_html_string(content)
    body = root.find("body")

    transform_document_before(body)

    # TODO
    # What is with this?
    for h1 in body.xpath('.//h1'):
        h1.tag = 'A1Heading'
        remove_attributes_for_element(h1)
        remove_newline(h1)

    for h2 in body.xpath('.//h2'):
        h2.tag = 'A8TitleAbbreviations'
        remove_attributes_for_element(h2)
        remove_newline(h2)
        if language == 'arabic':
            _check_for_arabic(h2)


    for p in body.xpath(".//p[@class='abbreviation-p']"):
        p.tag = 'A9TextAbbreviations'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)


    for p in body.xpath(".//p"):
        p.tag = 'A9TextAbbreviations'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)

    body = transform_document(body)

    return body


def export_preface(content, language):
    "Export preface page."

    root = parse_html_string(content)
    body = root.find("body")

    transform_document_before(body)

    # TODO
    # What is with this?
    for h1 in body.xpath('.//h1'):
        h1.tag = 'A1Heading'

        remove_attributes_for_element(h1)
        remove_newline(h1)


    # for p in body.xpath(".//p[@class='preface-quote']"):
    #     p.tag = 'A2BodyText'
    #     remove_attributes_for_element(p)

    for quote in body.xpath(".//div[@class='preface-quote']"):
        new_quote = etree.fromstring(etree.tostring(quote))
        new_quote.tag = 'PrefaceQuote'
        remove_attributes_for_element(new_quote)

        for p in new_quote.xpath('.//p'):
            p.tag = 'A10QuoteWide'
            remove_attributes_for_element(p)

            if p.text[0] in [u"\u201e", u"\u201d", u"\u201a", u"\u2019", u'"', u'“', u'„']:
                p.text = u' '+p.text

            if language == 'arabic':
                _check_for_arabic(p)

        for author in new_quote.xpath(".//div[@class='author']"):
            author.tag = 'A11QuoteReference'
            remove_attributes_for_element(author)
            if language == 'arabic':
                _check_for_arabic(author)

        body.insert(0, new_quote)
        quote.getparent().remove(quote)

    for p in body.xpath(".//p[@class='preface-p']"):
        p.tag = 'A2BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)


    for p in body.xpath(".//p"):
        p.tag = 'A2BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)

    handle_bold_and_italic_all(body)

    previous_tag = ''
    for elem in body.iter():
        if previous_tag in ['A6TitleContents', 'A1Heading']:
            if elem.tag == 'A2BodyText':
                elem.tag = 'A2BodyTextFirstPara'

        previous_tag = elem.tag

    body = transform_document(body)

    return body


def export_text(content, language):
    "Export text page."

    root = parse_html_string(content)
    body = root.find("body")

    transform_document_before(body)

    # TODO
    # What is with this?
    for h1 in body.xpath('.//h1'):
        h1.tag = 'B1Heading'
        remove_attributes_for_element(h1)
        remove_newline(h1)

    for s1 in body.xpath(".//span[@class='text-subtitle']"):
        s1.tag = 'B2ReferenceTitle'
        remove_attributes_for_element(s1)
        remove_newline(s1)
        if language == 'arabic':
            _check_for_arabic(s1)


    for h2 in body.xpath('.//h2'):
        h2.tag = 'B6HeadingText'
        remove_attributes_for_element(h2)
        remove_newline(h2)

    for p in body.xpath(".//p[@class='text-p']"):
        p.tag = 'B5BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)

    for quote in body.xpath(".//p[@class='text-inline-quote']"):
        quote.tag = 'B7QuoteBold'
        remove_attributes_for_element(quote)

        if quote.text and quote.text[0] in [u"\u201e", u"\u201d", u"\u201a", u"\u2019", u'"', u'“', u'„']:
            quote.text = u' '+quote.text

        if language == 'arabic':
            _check_for_arabic(quote)

    for quote in body.xpath(".//div[@class='text-quote']"):
        quote.tag = 'ForewordQuote2'
        imprint_pos = body.index(quote)

        remove_attributes_for_element(quote)

        # quote.tag = 'Imprint'
        # remove_attributes_for_element(imprint)

        for p in quote.xpath(".//p"):
            p.tag = 'B3Quote'

            remove_attributes_for_element(p)
            remove_newline(p)

            if p.text and p.text[0] in [u"\u201e", u"\u201d", u"\u201a", u"\u2019", u'"', u'“', u'„']:
                p.text = u' '+p.text

            if language == 'arabic':
                _check_for_arabic(p)

        for p in quote.xpath(".//div"):
            p.tag = 'B4QuoteReference'
            remove_attributes_for_element(p)
            remove_newline(p)

            if language == 'arabic':
                _check_for_arabic(p)

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
        remove_attributes_for_element(ol)

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
            remove_attributes_for_element(p)

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

                            if language == 'arabic':
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

                            if language == 'arabic':
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
                    if language == 'arabic':
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
                remove_newline(p)

                if text == u"":
                    p.drop_tree()


    for p in body.xpath(".//p"):
        p.tag = 'B5BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)

    handle_bold_and_italic_all(body)

    previous_tag = ''
    for elem in body.iter():
        if previous_tag in ['B6HeadingText', 'B1Heading', 'B4QuoteReference', 'B7QuoteBold', 'B3Quote']:
            if elem.tag == 'B5BodyText':
                elem.tag = 'B5BodyTextFirstPara'

        previous_tag = elem.tag

    body = transform_document(body)

    return body


def export_country(content, language):
    "Export country page."

    root = parse_html_string(content)
    body = root.find("body")

    transform_document_before(body)

    handle_facts(body.xpath(".//div[@class='country-fact']"))

    # Handle Intro text
    for intro in body.xpath(".//p[@class='country-intro-text']"):
        intro.tag = 'C4IntroText'
        remove_attributes_for_element(intro)
        remove_newline(intro)
        if language == 'arabic':
            _check_for_arabic(intro)

    for comment in body.xpath('.//a[@class="comment-link"]'):
        comment.drop_tree()

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
        remove_attributes_for_element(ol)

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
            remove_attributes_for_element(p)

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

                            if language == 'arabic':
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

                            if language == 'arabic':
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
                    if language == 'arabic':
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
                remove_newline(p)

                if text == u"":
                    p.drop_tree()

    for h1 in body.xpath('.//h1'):
        h1.tag = 'C1Heading'
        remove_attributes_for_element(h1)
        remove_newline(h1)

    for h2 in body.xpath('.//h2'):
        h2.tag = 'C5HeadingText'
        remove_attributes_for_element(h2)
        remove_newline(h2)

    for h3 in body.xpath('.//h3'):
        h3.tag = 'C10HeadingIntro'
        remove_attributes_for_element(h3)
        remove_newline(h3)

    for h4 in body.xpath('.//h4'):
        h4.tag = 'C9SubSubHeaderText'
        remove_attributes_for_element(h4)
        remove_newline(h4)

    for p in body.xpath('.//p'):
        p.tag = 'C6BodyText'
        remove_attributes_for_element(p)
        remove_newline(p)
        if language == 'arabic':
            _check_for_arabic(p)

    handle_bold_and_italic_all(body)

    previous_tag = ''
    for elem in body.iter():
        if previous_tag in ['C9SubSubHeaderText', 'C4IntroText', 'C5HeadingText', 'C10HeadingIntro']:
            if elem.tag == 'C6BodyText':
                elem.tag = 'C6BodyTextFirstPara'

        previous_tag = elem.tag


    body = transform_document(body)

    return body


def export_section(content, language):
    "Export country page."

    root = parse_html_string(content)
    body = root.find("body")

    section = etree.Element('Section')

    divider = body.xpath(".//div[@class='divider-content']")

    if divider:
        elements = divider[0].xpath(".//div")

        if len(elements) > 1:
            felem = etree.SubElement(section, 'First')
            felem.text =  "".join([x for x in elements[0].itertext()])

            selem = etree.SubElement(section, 'Second')
            selem.text =  "".join([x for x in elements[1].itertext()])

    return section


def modify_output_format(content):
    "Manually modify output content."

    # Country facts
    content = content.replace('<B3Quote/>', "")
    content = content.replace('<B3Quote></B3Quote>', "")
    content = content.replace('<B5BodyTextItalic class="fa fa-comment"></B5BodyTextItalic>', "")
    content = content.replace('</C3FactCountry2>', "</C3FactCountry2>\n")
    content = content.replace('</C2FactCountry1>', "</C2FactCountry1>\n")
    content = content.replace("</C8EndNote>\n  <C8EndNote>", "</C8EndNote> <C8EndNote>")
    content = content.replace('</content>', "</content>\n")
    content = content.replace("</A10QuoteWide><A11QuoteReference>", "</A10QuoteWide>\n<A11QuoteReference>")
    content = content.replace('</PrefaceQuote>', "</PrefaceQuote>\n")
    content = content.replace('<PrefaceQuote>', "<PrefaceQuote>\n")
    content = content.replace("</A4ImprintText>", "</A4ImprintText>\n")
    content = content.replace("</B3Quote><B4QuoteReference>", "</B3Quote>\n<B4QuoteReference>")
    content = content.replace("<document><content>", "<document>\n<content>")
    content = content.replace("<lineBelowFacts/></facts>", "<lineBelowFacts/>\n</facts>")
    content = content.replace("<lineaboveC8endNote/>", "<lineaboveC8endNote/>\n")

    content = content.replace("</A4ImprintText>\n</Imprint>", "</A4ImprintText></Imprint>")
    content = content.replace("</C8EndNote><C8EndNote>", "</C8EndNote>\n<C8EndNote>")
    content = content.replace(" <A8TitleAbbreviations>", "\n<A8TitleAbbreviations>")
    content = content.replace("<Section/>", "<Section/>\n")
    content = content.replace("<C4IntroText/>", "")
    content = content.replace(u"\uF020".encode('utf8'), "")
    content = content.replace(u"\xa0".encode('utf8'), " ")
    # Why was this ever here?!?!
#    content = content.replace(u"\xc2".encode('utf8'), " ")
    content = content.replace(u"\u2012".encode('utf8'), u"\u2013".encode('utf8'))
    content = content.replace(u"\u2013".encode('utf8'), u"\u2013".encode('utf8'))
    content = content.replace(u"\u2014".encode('utf8'), u"\u2013".encode('utf8'))
    content = content.replace(u"\ufe58".encode('utf8'), u"\u2013".encode('utf8'))
    content = content.replace(u"\ufe63".encode('utf8'), u"\u2013".encode('utf8'))
    content = content.replace(u"\uff0d".encode('utf8'), u"\u2013".encode('utf8'))
    content = content.replace("<A2BodyText/>", "")
    content = content.replace("<C5HeadingText/>", "")
    content = content.replace("<C10HeadingIntro/>", "")
    content = content.replace("<C8EndNoteItalic/>", "")
    content = content.replace("<C6BodyTextItalic></C6BodyTextItalic>", "")

    content = content.replace('##@@####@@##', '##@@##')
    content = content.replace(' ##@@## ', ' ')
    content = content.replace(' ##@@##', ' ')
    content = content.replace('##@@## ', ' ')


    def _check_line(line):
        st = line.lstrip()

        if len(st) > 1:
            if st[0] == '<':
                return st

        return line

    out = map(_check_line, content.split("\n"))
    content = "\n".join(out)

    c = re.compile("\n\s*\</content\>")
    content = c.sub("</content>", content)

    # end note
    c = re.compile("</C8EndNote>[\s\n]*</li>")
    content = c.sub("</C8EndNote></li>\n", content)

    # end note
    c = re.compile("<li>[\s\n]*</li>")
    content = c.sub("", content)

    # end note
    # New stuff because something changes and now we have extra white space before the content
    c = re.compile("<C8EndNote>[\s\n]*")
    content = c.sub("<C8EndNote>", content)

    TO_CHANGE = [("A1Heading", "A8TitleAbbreviations"),
        ("A1Heading", "A8TitleAbbreviations"),
        ("A2BodyTextFirstPara", "A2BodyText"),
        ("A2BodyText", "A2BodyText"),
        ("A2BodyText", "Imprint"),
        ("B5BodyTextFirstPara", "B5BodyText"),
        ("B5BodyText", "B5BodyText"),
        ("B5BodyText", "B6HeadingText"),
        ("C1Heading", "facts"),
        ("C1Heading", "C4IntroText"),
        ("C1Heading", "C6BodyText"),
        ("C4IntroText", "C5HeadingText"),
        ("C6BodyTextFirstPara", "C6BodyText"),
        ("C6BodyTextFirstPara", "C5HeadingText"),
        ("C6BodyText", "C6BodyText"),
        ("C6BodyText", "C5HeadingText"),
        ("C6BodyText", "C4IntroText"),
        ("C6BodyText", "C1Heading"),
        ("C5HeadingText", "C6BodyTextFirstPara"),
        ("C5HeadingText", "C4IntroText"),
        ("C5HeadingText", "C6BodyText"),
        ("C4IntroText", "C6BodyText"),
        ("C4IntroText", "C6BodyTextFirstPara"),
        ("C10HeadingText", "C10HeadingIntro"),
        ("C10HeadingIntro", "C4IntroText"),
        ("C10HeadingIntro", "C9SubSubHeaderText"),
        ("C4IntroText", "C4IntroText"),
        ("C5HeadingText", "C10HeadingIntro"),
        ("C5HeadingText", "C5HeadingText"),
        ("C5HeadingText", "C6HeadingText"),
        ("C6BodyTextFirstPara", "C9SubSubHeaderText"),
        ("C6BodyText", "C9SubSubHeaderText"),
        ("C6BodyText", "C5HeadingText"),
        ("C5HeadingText", "C9SubSubHeaderText"),
        ("C9SubSubHeaderText", "C6BodyText"),
        ("C9SubSubHeaderText", "C6BodyTextFirstPara"),
        ("C6BodyText", "C9SubSubHeaderText"),
        ("C6BodyText", "C8EndNotes"),
        ("C4IntroText", "C10HeadingIntro"),
        ("C10HeadingIntro", "C6BodyTextFirstPara"),
        ("C10HeadingIntro", "C6BodyText"),
        ("C6BodyTextFirstPara", "C8EndNotes"),
        ("A4ImprintTextFirstPara", "A4ImprintText"),
        ("B5BodyTextFirstPara", "B6HeadingText"),
        ("C6BodyTextFirstPara", "C9SubSubHeaderText"),
        ("C6BodyTextFirstPara", "C10HeadingIntro"),
        ("B3Quote", "B3Quote"),
        ("First", "Second"),
        ("Section", "content"),
        ("B6HeadingText", "B5BodyTextFirstPara"),
        ("B6HeadingText", "B5BodyText"),
        ("B6HeadingText", "B6HeadingText"),
        ("A1Heading", "A2BodyTextFirstPara"),
        ("A8TitleAbbreviations", "A9TextAbbreviations"),
        ("A1Heading", "A2BodyTextFirstPara"),
        ("A1Heading", "A2BodyText"),
        ("B1Heading", "ForewordQuote2"),
        ("B1Heading", "B5BodyTextFirstPara"),
        ("B1Heading", "B5BodyText"),
        ("B1Heading", "B7QuoteBold"),
        ("B1Heading", "B6HeadingText"),
        ("A9TextAbbreviations", "A9TextAbbreviations"),
        ("A9TextAbbreviations", "A8TitleAbbreviations"),
        ("B1Heading", "B2ReferenceTitle"),
        ("B7QuoteBold", "B5BodyText"),
        ("B7QuoteBold", "B7QuoteBold"),
        ("B7QuoteBold", "B2ReferenceTitle"),
        ("C8EndNote", "C8EndNote")
    ]

    for tag_one, tag_two in TO_CHANGE:
        c = re.compile("</{}>[^<]*<{}>".format(tag_one, tag_two))
        content = c.sub("</{}>\n<{}>".format(tag_one, tag_two), content)


    # c = re.compile("</{}>[\s\n\&nbsp\;]*<{}>".format('C6BodyTextFirstPara', 'C5HeadingText'))
    # content = c.sub("</{}>\n<{}>".format('C6BodyTextFirstPara', 'C5HeadingText'), content)

    c = re.compile("\n[\s\n]*\n")
    content = c.sub("\n", content)

    c = re.compile("<C6BodyText>[\s\n]*</C6BodyText>[\s\n]*")
    content = c.sub("", content)


    c = re.compile("<facts>[\s\n]*<C3FactCountry2>")
    content = c.sub("<facts><C3FactCountry2>", content)

    c = re.compile("<C8EndNotes>[\s\n]*<lineaboveC8endNote/>")
    content = c.sub("<C8EndNotes><lineaboveC8endNote/>", content)

    content = content.replace("<C8EndNote> ", "<C8EndNote>")
    # This should not be here. We have to check why is it not deleted at the normal place
    content = content.replace("<C6BodyText/>", "")
    content = content.replace("<B5BodyText/>", "")
    content = content.replace("\n</C5HeadingText>", "</C5HeadingText>")
    content = content.replace("</ForewordQuote2>", "</ForewordQuote2>\n")
    content = content.replace("</B2ReferenceTitle>", "</B2ReferenceTitle>\n")
    content = content.replace("<document>\n<content>", "<document><content>")
    content = content.replace("<C6BodyText></C6BodyText>\n", "")
    content = content.replace("</facts>\n<C4IntroText>", "</facts><C4IntroText>")

#    content = content.replace('>##@@##', '>')
    content = content.replace('##@@##</A2BodyTextFirstPara>', '</A2BodyTextFirstPara>')
    content = content.replace('##@@##</A2BodyText>', '</A2BodyText>')
    content = content.replace('##@@##</B5BodyTextFirstPara>', '</B5BodyTextFirstPara>')
    content = content.replace('##@@##</B5BodyText>', '</B5BodyText>')
    content = content.replace('##@@##</C3FactCountry2>', '</C3FactCountry2>')
    content = content.replace('##@@##</C2FactCountry1>', '</C2FactCountry1>')
    content = content.replace('##@@##</C6BodyTextFirstPara>', '</C6BodyTextFirstPara>')
    content = content.replace('##@@##</C6BodyText>', '</C6BodyText>')
    content = content.replace('##@@##</C8EndNote>', '</C8EndNote>')
    content = content.replace('##@@##</C1Heading>', '</C1Heading>')
    content = content.replace('##@@##</C5HeadingText>', '</C5HeadingText>')
    content = content.replace('##@@##</sup>', '</sup>')
    content = content.replace('##@@##</C9SubSubHeaderText>', '</C9SubSubHeaderText>')
    content = content.replace('##@@##</Second>', '</Second>')
    content = content.replace('##@@##</C4IntroText>', '</C4IntroText>')
    content = content.replace('<C6BodyTextFirstPara>##@@##', '<C6BodyTextFirstPara>')
    content = content.replace('<C6BodyText>##@@##', '<C6BodyText>')
    content = content.replace('<B5BodyTextFirstPara>##@@##', '<B5BodyTextFirstPara>')
    content = content.replace('<B5BodyText>##@@##', '<B5BodyText>')
    content = content.replace('<C1Heading>##@@##', '<C1Heading>')
    content = content.replace('<C5HeadingText>##@@##', '<C5HeadingText>')
    content = content.replace(' </C8EndNote>', '</C8EndNote>')

    content = content.replace('<B5BodyTextBold></B5BodyTextBold>', '')

    c = re.compile("</facts>[^<]*<C4IntroText>")
    content = c.sub("</facts><C4IntroText>", content)


#    content = content.replace("##@@##", "&#x00A0;")
    # This is really wery stupid but there is not time to play with lxml entities and what managing .text and .tail
    # on elements start to do after that
    content = content.replace("##@@##", "&nbsp;")
    content = content.replace("@!@!", "<nonarabic>")
    content = content.replace("#!#!", "</nonarabic>")
    content = content.replace("<nonarabic><nonarabic>", "<nonarabic>")
    content = content.replace("</nonarabic></nonarabic>", "</nonarabic>")
    content = content.replace("<nonarabic>:", ":<nonarabic>")

    c = re.compile("\$\$\#\#\$\$[\s]*")
#    content = c.sub(chr(0xa), content)
    content = c.sub("SOFTLINEBREAK", content)

    # Why doesn't strip_tag work?
    content = content.replace("<b>", "")
    content = content.replace("</b>", "")
    content = content.replace("<i>", "")
    content = content.replace("</i>", "")
    content = content.replace("<sup></sup>", "")

    c = re.compile("\n[\s\n]*\n")
    content = c.sub("\n", content)

    return content


def dump_site(book, book_version):
    "Django view for dumping Adobe InDesign XML file."

    from amnesty.common import read_toc_structure, read_toc_structure_order
    from booki.editor import models

    root = etree.Element("document")

    try:
        language = models.Info.objects.get(book=book, name='amnesty_language').get_value()
    except models.Info.DoesNotExist:
        language = 'english'

    toc = read_toc_structure(language)

    for chapter_name in read_toc_structure_order(language):
        try:
            chapter = models.Chapter.objects.get(version=book.version, url_title=chapter_name)
        except models.Chapter.MultipleObjectsReturned:
            print 'ERROR. THIS DOCUMENT WAS CREATED WITH WRONG STRUCTURE.'
            continue
        except models.Chapter.DoesNotExist:
            print '=========================='
            print 'ERROR. CAN NOT FIND CHAPTER ', chapter_name
            continue

        name = chapter.url_title

        # Just for the silly test document
        # if name == 'foreword':
        #     name = 'human-rights-know-no-border'

        item_obj = toc.get(name, None)


        if item_obj is None:
            if chapter.url_title == 'intro':
                item_obj = {'type': 'imprint'}
            if chapter.url_title in ['section3', 'separator-page-title-page', 'separator-page-section-start-part-1', 'separator-page-section-start-part-2-a-z-country-entries']:
                item_obj = {'type': 'section'}

        # This is really wery stupid but there is not time to play with lxml entities and what managing .text and .tail
        # on elements start to do after that
        content = chapter.content.replace('&nbsp;', '##@@##')

        if item_obj["type"] == "country":
            root.append(export_country(content, language))
        elif item_obj["type"] == "first":
            root.append(export_first(content, language))
        elif item_obj["type"] == "text":
            root.append(export_text(content, language))
        elif item_obj["type"] == "abbreviations":
            root.append(export_abbreviation(content, language))
        elif item_obj["type"] == "preface":
            root.append(export_preface(content, language))
        elif item_obj["type"] == "section":
            root.append(export_section(content, language))

    etree.strip_tags(root, 'b')
    etree.strip_tags(root, 'i')
    etree.strip_tags(root, 'u')
    etree.strip_tags(root, 'strong')
    etree.strip_tags(root, 'div')
    etree.strip_tags(root, 'span')

    export_content = etree.tostring(root, pretty_print=False, encoding="utf-8", xml_declaration=True)
    export_content = modify_output_format(export_content)

    return export_content