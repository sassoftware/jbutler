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
from threading import Thread
import os

from jbutler.jenkinsapi import jenkins
from jbutler.lib import jobs
import jenkinsapi

from .. import base
from ..base import mock


class DeleteJobsTestCase(base.JbutlerTestCase):
    """Tests for jobs delete"""

    def setUp(self):
        super(DeleteJobsTestCase, self).setUp()

        self.foo_filename = os.path.join(self.work_dir, 'jobs', 'foo.xml')

        Jenkins_patcher = mock.patch(
            'jbutler.utils.jenkins_utils.Jenkins')
        self.addCleanup(Jenkins_patcher.stop)
        self.Jenkins = Jenkins_patcher.start()

        click_patcher = mock.patch('jbutler.lib.jobs.click')
        self.addCleanup(click_patcher.stop)
        self.click = click_patcher.start()

    def test_delete_jobs(self):
        self.Jenkins.return_value.has_job.return_value = True

        expected = ['foo']
        actual = jobs.deleteJobs(self.Jenkins(), [self.foo_filename])

        self.assertEqual(expected, actual)
        self.Jenkins.return_value.delete_job.assert_called_once_with('foo')

    def test_delete_jobs_multiple(self):
        bar_filename = os.path.join(self.work_dir, 'jobs', 'bar.xml')

        self.Jenkins.return_value.has_job.side_effect = (True, True)

        expected = ['foo', 'bar']
        actual = jobs.deleteJobs(self.Jenkins(), [self.foo_filename,
                                                  bar_filename])

        self.assertEqual(actual, expected)
        self.assertEqual([mock.call('foo'), mock.call('bar')],
                         self.Jenkins.return_value.has_job.call_args_list)
        self.assertEqual([mock.call('foo'), mock.call('bar')],
                         self.Jenkins.return_value.delete_job.call_args_list)

    def test_delete_jobs_missing_job(self):
        bar_filename = os.path.join(self.work_dir, 'jobs', 'bar.xml')

        self.Jenkins.return_value.has_job.side_effect = (True, False)

        expected = ['foo']
        actual = jobs.deleteJobs(self.Jenkins(), [self.foo_filename,
                                                  bar_filename])

        self.assertEqual(expected, actual)
        self.assertEqual([mock.call('foo'), mock.call('bar')],
                         self.Jenkins.return_value.has_job.call_args_list)
        self.Jenkins.return_value.delete_job.assert_called_once_with('foo')
        self.click.echo.assert_called_once_with('warning: no such job: '
                                                "'bar'", err=True)


class UpdateJobsTests(base.JbutlerTestCase):
    """Tests for update job"""

    def setUp(self):
        super(UpdateJobsTests, self).setUp()

        Jenkins_patcher = mock.patch('jbutler.utils.jenkins_utils.Jenkins')
        self.addCleanup(Jenkins_patcher.stop)
        self.Jenkins = Jenkins_patcher.start()
        self.Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)

        click_patcher = mock.patch('jbutler.lib.jobs.click')
        self.addCleanup(click_patcher.stop)
        self.click = click_patcher.start()

    def test_update_job(self):
        _foo = mock.MagicMock(spec=jenkinsapi.job.Job)
        _foo.name = 'foo'

        def has_job(name):
            return name == 'foo'

        self.Jenkins.return_value.has_job.side_effect = has_job

        def get_job(name):
            if name == 'foo':
                return _foo

        self.Jenkins.return_value.get_job.side_effect = get_job

        _file = mock.MagicMock()
        _file.name = 'jobs/foo.xml'
        _file.read.return_value = 'A foo job'
        actual = jobs.updateJobs(self.Jenkins(), [_file])
        self.assertListEqual([_foo], actual)
        self.assertListEqual([mock.call('foo')],
                             self.Jenkins.return_value.has_job.call_args_list)
        _foo.update_config.assert_called_once_with('A foo job')
        self.assertListEqual([], self.click.echo.call_args_list)

    def test_update_job_multiple(self):
        _foo = mock.MagicMock(spec=jenkinsapi.job.Job)
        _foo.name = 'foo'
        _bar = mock.MagicMock(spec=jenkinsapi.job.Job)
        _bar.name = 'bar'

        def has_job(name):
            return name == 'foo' or name == 'bar'

        self.Jenkins.return_value.has_job.side_effect = has_job

        def get_job(name):
            if name == 'foo':
                return _foo
            elif name == 'bar':
                return _bar

        self.Jenkins.return_value.get_job.side_effect = get_job

        _foo_file = mock.MagicMock()
        _foo_file.name = 'jobs/foo.xml'
        _foo_file.read.return_value = 'A foo job'
        _bar_file = mock.MagicMock()
        _bar_file.name = 'jobs/bar.xml'
        _bar_file.read.return_value = 'A bar job'
        actual = jobs.updateJobs(self.Jenkins(), [_foo_file, _bar_file])
        self.assertListEqual([_foo, _bar], actual)
        self.assertListEqual([mock.call('foo'), mock.call('bar')],
                             self.Jenkins.return_value.has_job.call_args_list)
        _foo.update_config.assert_called_once_with('A foo job')
        _bar.update_config.assert_called_once_with('A bar job')
        self.assertListEqual([], self.click.echo.call_args_list)

    def test_update_job_missing_job(self):
        _foo = mock.MagicMock(spec=jenkinsapi.job.Job)
        _foo.name = 'foo'
        _bar = mock.MagicMock(spec=jenkinsapi.job.Job)
        _bar.name = 'bar'

        def has_job(name):
            return name == 'foo'

        self.Jenkins.return_value.has_job.side_effect = has_job

        def get_job(name):
            if name == 'foo':
                return _foo

        self.Jenkins.return_value.get_job.side_effect = get_job
        _foo_file = mock.MagicMock()
        _foo_file.name = 'jobs/foo.xml'
        _foo_file.read.return_value = 'A foo job'
        _bar_file = mock.MagicMock()
        _bar_file.name = 'jobs/bar.xml'
        actual = jobs.updateJobs(self.Jenkins(), [_foo_file, _bar_file])
        self.assertListEqual([_foo], actual)
        self.assertEqual(
            [mock.call('foo'), mock.call('bar')],
            self.Jenkins.return_value.has_job.call_args_list)
        _foo.update_config.assert_called_once_with('A foo job')
        self.click.echo.assert_called_once_with("warning: no such job: 'bar'",
                                                err=True)


class BuildJobsTests(base.JbutlerTestCase):
    def setUp(self):
        super(BuildJobsTests, self).setUp()

        Jenkins_patcher = mock.patch('jbutler.utils.jenkins_utils.Jenkins')
        self.Jenkins = Jenkins_patcher.start()
        self.addCleanup(Jenkins_patcher.stop)
        self.Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)

        click_patcher = mock.patch('jbutler.lib.jobs.click')
        self.click = click_patcher.start()
        self.addCleanup(click_patcher.stop)

        threading_patcher = mock.patch('jbutler.lib.jobs.threading')
        self.threading = threading_patcher.start()
        self.addCleanup(threading_patcher.stop)
        self.threading.Thread = mock.MagicMock(spec=Thread)

    def test_build_missing_job(self):
        self.Jenkins.return_value.has_job.return_value = False
        self.threading.active_count.return_value = 0

        jobs.buildJobs(self.Jenkins(), ['foo'])
        self.assertEqual(self.threading.Thread.call_args_list, [])
