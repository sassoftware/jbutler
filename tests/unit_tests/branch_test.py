#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from jbutler import errors
from jbutler.lib import branch
from lxml import etree

from .. import base
from ..base import mock


class BranchTestCase(base.JbutlerTestCase):
    def setUp(self):
        super(BranchTestCase, self).setUp()
        self.xml = ('<foo>'
                    '<bar>text to update</bar>'
                    '<baz>some other text</baz>'
                    '</foo>')
        self.doc = etree.fromstring(self.xml)
        self.macros = {'data': 'some data'}
        self.paths = {'/foo/bar': '%(data)s'}
        self.to_macros = {'data': 'some data'}
        self.from_macros = {'data': 'some old data'}
        self.job_dir = '/jobs'

    def test_update_job_data(self):
        expected = b'<foo><bar>some data</bar><baz>some other text</baz></foo>'
        newDoc = branch._update_job_data(self.doc, self.paths, self.to_macros)
        self.assertEqual(etree.tostring(newDoc), expected)

        expected = b'<foo><bar>some data</bar><baz>no template</baz></foo>'
        self.paths['/foo/baz'] = 'no template'
        newDoc = branch._update_job_data(self.doc, self.paths, self.to_macros)
        self.assertEqual(etree.tostring(newDoc), expected)

    def test_update_job_data_elements_error(self):
        self.paths['/foo/spam'] = '%(data)s 2'
        with self.assertRaises(errors.TemplateError) as cm:
            branch._update_job_data(self.doc, self.paths, self.to_macros)
            self.assertEqual("no element matching xpath '/foo/spam'",
                             str(cm.exception))

    def test_update_job_data_extra_templates(self):
        expected = (b'<foo><bar>some data</bar><baz>some other text</baz>'
                    b'<bar>Another bar</bar></foo>')
        newBar = etree.SubElement(self.doc, 'bar')
        newBar.text = 'Another bar'
        newDoc = branch._update_job_data(self.doc, self.paths, self.to_macros)
        self.assertEqual(etree.tostring(newDoc), expected)

    @mock.patch('jbutler.lib.branch._update_job_data')
    @mock.patch('jbutler.lib.branch.warnings')
    @mock.patch('jbutler.lib.branch.utils')
    def test_branch_jobs(self, _utils, _warnings, _update_job_data):
        from_macros = {'branch': 'foo'}
        to_macros = {'branch': 'bar'}
        templateList = ['template']

        _utils.readJob.return_value = 'job'
        _utils.readTemplate.return_value = {
            'name': '/jobs/%(branch)s.xml',
            'templates': [],
        }

        _update_job_data.side_effect = [
            errors.TemplateError('error'),
            'newJob',
        ]
        try:
            branch.branch_jobs(templateList, from_macros, to_macros,
                               self.job_dir)
        except errors.CommandError as err:
            self.assertEqual(str(err), "error parsing job '/jobs/foo.xml'")
        else:
            self.fail('Did not raise %s' % errors.CommandError)

        branch.branch_jobs(templateList, from_macros, to_macros, self.job_dir)
        branch.utils.readTemplate.assert_called_with('template')
        branch.utils.readJob.assert_called_with('/jobs/foo.xml')
        branch.utils.writeJob.assert_called_with('/jobs/bar.xml', 'newJob')
        branch.warnings.warn.assert_not_called()

    @mock.patch('jbutler.lib.branch._update_job_data')
    @mock.patch('jbutler.lib.branch.warnings')
    @mock.patch('jbutler.lib.branch.utils')
    def test_branch_jobs_template_macros(self, _utils, _warnings,
                                         _update_job_data):
        from_macros = None
        to_macros = {'branch': 'bar'}
        templateList = ['template']

        _utils.readJob.return_value = 'job'
        _utils.readTemplate.return_value = {
            'name': '/jobs/%(branch)s.xml',
            'templates': [],
            'macros': [
                ['branch', 'foo'],
            ]
        }
        _utils.parseMacros.return_value = {'branch': 'foo'}
        _update_job_data.return_value = 'newJob'

        branch.branch_jobs(templateList, from_macros, to_macros, self.job_dir)
        branch.utils.readTemplate.assert_called_with('template')
        branch.utils.readJob.assert_called_with('/jobs/foo.xml')
        branch.utils.writeJob.assert_called_with('/jobs/bar.xml', 'newJob')
        branch.warnings.warn.assert_called_with(
            'Support for macros stored in templates is deprecated.',
            DeprecationWarning,
        )

    @mock.patch('jbutler.lib.branch._update_job_data')
    @mock.patch('jbutler.lib.branch.warnings')
    @mock.patch('jbutler.lib.branch.utils')
    def test_branch_jobs_template_macros_templateerror(self, _utils, _warnings,
                                                       _update_job_data):
        from_macros = None
        to_macros = {'branch': 'bar'}
        templateList = ['template']

        _utils.readJob.return_value = 'job'
        _utils.readTemplate.return_value = {'name': '/jobs/%(branch)s.xml',
                                            'templates': [],
                                            'macros': [('branch', 'foo')],
                                            }
        _utils.parseMacros.return_value = {'branch': 'foo'}
        _update_job_data.side_effect = [errors.TemplateError('error'),
                                        'newJob',
                                        ]

        with self.assertRaises(errors.CommandError) as cm:
            branch.branch_jobs(templateList, from_macros, to_macros,
                               self.job_dir)
            self.assertEqual(str(cm.exception),
                             "error parsing job '/jobs/foo.xml'")

        branch.warnings.warn.assert_called_with(
            'Support for macros stored in templates is deprecated.',
            DeprecationWarning,
        )
