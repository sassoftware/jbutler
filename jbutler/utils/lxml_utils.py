#
# Copyright (c) 2013 SAS Institute, Inc
#

from lxml import etree


parser = etree.XMLParser(encoding='utf-8', recover=True)


def fromstring(s):
    '''Wrap around etree.fromstring to ensure we don't pass unicode strings
    to lxml
    '''
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return etree.fromstring(s, parser)


def parse(fh):
    return etree.parse(fh, parser)


def tostring(obj):
    return etree.tostring(
        obj,
        xml_declaration=True,
        encoding='UTF-8',
        pretty_print=True,
        )
