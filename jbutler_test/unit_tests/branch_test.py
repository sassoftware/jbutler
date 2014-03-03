#
# Copyright (c) SAS Institute Inc.
#


from conary.build import macros as conarymacros
from jbutler import errors as jberrors
from jbutler.commands import branchcommand as bc
from lxml import etree
from testutils import mock

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
        self.bc = bc.BranchCommand()
        self.bc.toMacros = conarymacros.Macros({'data': 'some data'})
        self.bc.fromMacros = conarymacros.Macros({'data': 'some old data'})
        self.bc.jobDir = '/jobs'

    def test_updateJobData(self):
        expected = ("<foo>"
                    "<bar>some data</bar>"
                    "<baz>some other text</baz>"
                    "</foo>")
        newDoc = self.bc._updateJobData(self.doc, self.paths)
        self.assertEqual(etree.tostring(newDoc), expected)

        expected = ("<foo>"
                    "<bar>some data</bar>"
                    "<baz>no template</baz>"
                    "</foo>")
        self.paths['/foo/baz'] = 'no template'
        newDoc = self.bc._updateJobData(self.doc, self.paths)
        self.assertEqual(etree.tostring(newDoc), expected)

    def test_updateJobData_elements_error(self):
        self.paths['/foo/spam'] = '%(data)s 2'
        err = self.assertRaises(
            jberrors.TemplateError,
            self.bc._updateJobData,
            self.doc,
            self.paths,
            )
        self.assertEqual(str(err), "no element matching xpath '/foo/spam'")

    def test_updateJobData_extra_templates(self):
        expected = ("<foo>"
                    "<bar>some data</bar>"
                    "<baz>some other text</baz>"
                    "<bar>Another bar</bar>"
                    "</foo>")
        newBar = etree.SubElement(self.doc, 'bar')
        newBar.text = "Another bar"
        newDoc = self.bc._updateJobData(self.doc, self.paths)
        self.assertEqual(etree.tostring(newDoc), expected)

    def test_branch_jobs(self):
        self.bc.fromMacros = conarymacros.Macros({'branch': 'foo'})
        self.bc.toMacros = conarymacros.Macros({'branch': 'bar'})
        mock.mock(bc.utils, 'readJob', 'job')
        mock.mock(bc.utils, 'readTemplate', {
            'name': '/jobs/%(branch)s.xml',
            'templates': [],
            })
        mock.mock(bc.utils, 'writeJob')
        mock.mockMethod(self.bc._updateJobData, 'newJob')

        templateList = ['template']

        self.bc.branchJobs(templateList)
        bc.utils.readTemplate._mock.assertCalled('template')
        bc.utils.readJob._mock.assertCalled('/jobs/foo.xml')
        bc.utils.writeJob._mock.assertCalled('/jobs/bar.xml', 'newJob')

        self.bc._updateJobData._mock.raiseErrorOnAccess(
            jberrors.TemplateError('error'))
        err = self.assertRaises(
            jberrors.CommandError,
            self.bc.branchJobs,
            templateList,
            )
        self.assertEqual(str(err), "error parsing job '/jobs/foo.xml'")
