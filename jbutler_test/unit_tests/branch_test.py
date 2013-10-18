#
# Copyright (c) SAS Institute Inc.
#


from conary.build import macros as conarymacros
from jbutler import errors as jberrors
from jbutler.lib import branch
from lxml import etree

from jbutler_test import jbutlerhelp


class BranchTests(jbutlerhelp.JButlerHelper):
    def setUp(self):
        jbutlerhelp.JButlerHelper.setUp(self)
        self.xml = ("<foo>"
                    "<bar>text to update</bar>"
                    "<baz>some other text</baz>"
                    "</foo>")
        self.doc = etree.fromstring(self.xml)
        self.macros = conarymacros.Macros({'data': 'some data'})
        self.paths = {
            '/foo/bar': '%(data)s',
            }

    def test_updateJobData(self):
        expected = ("<foo>"
                    "<bar>some data</bar>"
                    "<baz>some other text</baz>"
                    "</foo>")
        newDoc = branch._updateJobData(self.doc, self.paths, self.macros)
        self.assertEqual(etree.tostring(newDoc), expected)

        expected = ("<foo>"
                    "<bar>some data</bar>"
                    "<baz>no template</baz>"
                    "</foo>")
        self.paths['/foo/baz'] = 'no template'
        newDoc = branch._updateJobData(self.doc, self.paths, self.macros)
        self.assertEqual(etree.tostring(newDoc), expected)

    def test_updateJobData_elements_error(self):
        self.paths['/foo/spam'] = '%(data)s 2'
        self.assertRaises(jberrors.TemplateError, branch._updateJobData,
                          self.doc, self.paths, self.macros)

    def test_updateJobData_extra_templates(self):
        expected = ("<foo>"
                    "<bar>some data</bar>"
                    "<baz>some other text</baz>"
                    "<bar>Another bar</bar>"
                    "</foo>")
        newBar = etree.SubElement(self.doc, 'bar')
        newBar.text = "Another bar"
        newDoc = branch._updateJobData(self.doc, self.paths, self.macros)
        self.assertEqual(etree.tostring(newDoc), expected)
