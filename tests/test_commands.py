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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import os

from click import exceptions as cexc

from . import base
from .base import mock


class ConfigCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs command and sub-commands"""

    def test_successful_config_show(self):
        result = self.run_command('config', exit_code=0)
        expected = ('[jbutler]\n'
                    'jobdir = jobs\n'
                    'password = <obscured>\n'
                    'server = http://jenkins.example.com\n'
                    'ssl_verify = true\n'
                    'templatedir = templates\n'
                    'username = test\n'
                    )
        self.assertEqual(expected, result.output)

    def test_successful_config_show_exposed_password(self):
        result = self.run_command('config --show-password', exit_code=0)
        expected = ('[jbutler]\n'
                    'jobdir = jobs\n'
                    'password = secret\n'
                    'server = http://jenkins.example.com\n'
                    'ssl_verify = true\n'
                    'templatedir = templates\n'
                    'username = test\n'
                    )
        self.assertEqual(expected, result.output)

    def test_successful_config_show_alt_config_file(self):
        self.mkfile('jbutlerrc_alt',
                    contents='[jbutler]\ntemplatedir = other/path\n')
        args = '--config-file=./jbutlerrc_alt config'
        result = self.run_command(args, exit_code=0)
        expected = ('[jbutler]\n'
                    'jobdir = jobs\n'
                    'password = <obscured>\n'
                    'server = http://jenkins.example.com\n'
                    'ssl_verify = true\n'
                    'templatedir = other/path\n'
                    'username = test\n'
                    )
        self.assertEqual(expected, result.output)


class JobsCreateCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs command and sub-commands"""

    def setUp(self):
        super(JobsCreateCommandTest, self).setUp()

        def has_job(name):
            return False

        self.Jenkins.return_value.has_job.side_effect = has_job

    def test_create_no_jobs(self):
        with self.assertRaises(cexc.MissingParameter):
            result = self.run_command('jobs create', exit_code=2)
            self.assertIn('Error: Missing argument "jobs"', result.output)

        with self.assertRaises(cexc.BadParameter):
            result = self.run_command('jobs create jobs/foo.xml '
                                      'jobs/spam.xml', exit_code=2)
            self.assertIn('Error: Invalid value for "jobs": Could not open '
                          'file: jobs/spam.xml: No such file or directory',
                          result.output)

    def test_successful_job_creation(self):
        result = self.run_command('jobs create jobs/foo.xml', exit_code=0)
        self.assertEqual('', result.output)
        self.assertEqual(0, result.exit_code)

        # verify JenkinsAPI asked to create job
        self.Jenkins.return_value.create_job.assert_called_once_with(
            'foo', base.FOO_JOB)

    def test_successful_job_creation_with_list(self):
        result = self.run_command('jobs create jobs/foo.xml jobs/bar.xml',
                                  exit_code=0)
        self.assertEqual('', result.output)

        # verify JenkinsAPI asked to create job
        self.assertListEqual(
            [mock.call('foo', base.FOO_JOB), mock.call('bar', base.BAR_JOB)],
            self.Jenkins.return_value.create_job.call_args_list,
        )

    def test_existing_job(self):
        def has_job(name):
            return name in self.jobs

        self.Jenkins.return_value.has_job.side_effect = has_job

        result = self.run_command('jobs create jobs/foo.xml', exit_code=0)
        self.assertEqual("warning: job already exists on server: 'foo'\n",
                         result.output)
        self.Jenkins.return_value.create_job.assert_not_called()


class JobsRetrieveCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs retrieve sub-command"""

    def setUp(self):
        super(JobsRetrieveCommandTest, self).setUp()
        for f in os.listdir('./jobs'):
            os.remove(os.path.join(self.work_dir, 'jobs', f))

    def test_successful_job_retrieval(self):
        result = self.run_command('jobs retrieve', exit_code=0)
        self.assertEqual('', result.output)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertListEqual(
            [mock.call('foo'), mock.call('bar'), mock.call('baz')],
            self.Jenkins.return_value.get_job.call_args_list)

        # check for files
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/bar.xml'))
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/baz.xml'))
        with open(self.work_dir + '/jobs/foo.xml') as fh:
            self.assertEqual(fh.read(), base.FOO_JOB)
        with open(self.work_dir + '/jobs/bar.xml') as fh:
            self.assertEqual(fh.read(), base.BAR_JOB)
        with open(self.work_dir + '/jobs/baz.xml') as fh:
            self.assertEqual(fh.read(), base.BAZ_JOB)

    def test_successful_job_retrieval_with_list(self):
        result = self.run_command('jobs retrieve foo', exit_code=0)
        self.assertEqual('', result.output)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertListEqual(
            [mock.call('foo')],
            self.Jenkins.return_value.get_job.call_args_list)

        # check for files
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/bar.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/baz.xml'))
        with open(self.work_dir + '/jobs/foo.xml') as fh:
            self.assertEqual(fh.read(), base.FOO_JOB)

    def test_successful_job_retrieval_with_missing_item(self):
        # server only has the foo job
        self.Jenkins.return_value.get_jobs_info.return_value = iter([
            ('foourl', 'foo'),
        ])

        result = self.run_command('jobs retrieve foo bar', exit_code=0)
        self.assertEqual("warning: no such job: 'bar'\n", result.output)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertListEqual(
            [mock.call('foo')],
            self.Jenkins.return_value.get_job.call_args_list)

        # check for files
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/bar.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/baz.xml'))
        with open(self.work_dir + '/jobs/foo.xml') as fh:
            self.assertEqual(fh.read(), base.FOO_JOB)

    def test_retrieval_filter_simple(self):
        result = self.run_command('jobs retrieve --filter=foo', exit_code=0)
        self.assertEqual('', result.output)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertListEqual(
            [mock.call('foo')],
            self.Jenkins.return_value.get_job.call_args_list)

        # check for files
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/bar.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/baz.xml'))
        with open(self.work_dir + '/jobs/foo.xml') as fh:
            self.assertEqual(fh.read(), base.FOO_JOB)

    def test_retrieval_filter_glob(self):
        result = self.run_command('jobs retrieve --filter=f.*', exit_code=0)
        self.assertEqual('', result.output)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertListEqual(
            [mock.call('foo')],
            self.Jenkins.return_value.get_job.call_args_list)

        # check for files
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/bar.xml'))
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/baz.xml'))
        with open(self.work_dir + '/jobs/foo.xml') as fh:
            self.assertEqual(fh.read(), base.FOO_JOB)

    def test_retrieval_filter_glob2(self):
        result = self.run_command(['jobs', 'retrieve', '--filter', 'ba*'],
                                  exit_code=0)
        self.assertEqual('', result.output)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertEqual(
            [mock.call('bar'), mock.call('baz')],
            self.Jenkins.return_value.get_job.call_args_list)

        # check for files
        self.assertFalse(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/bar.xml'))
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/baz.xml'))
        with open(self.work_dir + '/jobs/bar.xml') as fh:
            self.assertEqual(fh.read(), base.BAR_JOB)
        with open(self.work_dir + '/jobs/baz.xml') as fh:
            self.assertEqual(fh.read(), base.BAZ_JOB)


class JobsDisableCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs command and sub-commands"""

    def test_disable_no_jobs(self):
        with self.assertRaises(cexc.MissingParameter):
            result = self.run_command('jobs disable', exit_code=2)
            self.assertIn('Missing argument "jobs"', result.output)

        with self.assertRaises(cexc.BadParameter):
            result = self.run_command(
                'jobs disable jobs/foo.xml jobs/spam.xml', exit_code=2)
            self.assertIn('Error: Invalid value for "jobs": Path '
                          '"jobs/spam.xml" does not exist.', result.output)

    def test_disable(self):
        result = self.run_command('jobs disable jobs/foo.xml', exit_code=0)
        self.assertEqual('', result.output)
        self.assertIn('<disabled>false</disabled>',
                      open(self.work_dir + '/jobs/foo.xml').read())
        self.jobs['foo'].disable.assert_called_once_with()

    def test_disable_force(self):
        result = self.run_command('jobs disable --force jobs/foo.xml',
                                  exit_code=0)
        self.assertEqual('', result.output)
        self.assertEqual(0, result.exit_code)
        self.assertIn('<disabled>true</disabled>',
                      open(self.work_dir + '/jobs/foo.xml').read())
        self.jobs['foo'].disable.assert_called_once_with()


class JobsEnableCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs command and sub-commands"""

    def test_enable_no_jobs(self):
        with self.assertRaises(cexc.MissingParameter):
            result = self.run_command('jobs enable', exit_code=2)
            self.assertIn('Missing argument "jobs"', result.output)

    def test_enable(self):
        self.mkfile('jobs/foo.xml',
                    contents=base.FOO_JOB.replace('false', 'true'))

        self.jobs['foo'].is_enabled.return_value = False

        result = self.run_command('jobs enable jobs/foo.xml', exit_code=0)
        self.assertEqual('', result.output)
        self.assertIn('<disabled>true</disabled>',
                      open(self.work_dir + '/jobs/foo.xml').read())
        self.jobs['foo'].enable.assert_called_once_with()

    def test_enable_force(self):
        self.mkfile('jobs/foo.xml',
                    contents=base.FOO_JOB.replace('false', 'true'))

        self.jobs['foo'].is_enabled.return_value = False

        result = self.run_command('jobs enable --force jobs/foo.xml',
                                  exit_code=0)
        self.assertEqual('', result.output)
        self.assertIn('<disabled>false</disabled>',
                      open(self.work_dir + '/jobs/foo.xml').read())
        self.jobs['foo'].enable.assert_called_once_with()


class JobsDeleteCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs command and sub-commands"""

    def test_delete_no_jobs(self):
        with self.assertRaises(cexc.MissingParameter):
            result = self.run_command('jobs delete', exit_code=2)
            self.assertIn('Missing argument "jobs"', result.output)

    def test_delete(self):
        result = self.run_command('jobs delete jobs/foo.xml', exit_code=0)
        self.assertEqual('', result.output)

        self.assertTrue(os.path.exists(self.work_dir + '/jobs/foo.xml'))
        self.assertEqual(
            [mock.call('foo')],
            self.Jenkins.return_value.delete_job.call_args_list,
        )

    def test_delete_missing_job(self):
        self.mkfile('jobs/spam.xml', contents=base.BAR_JOB)

        result = self.run_command('jobs delete jobs/spam.xml', exit_code=0)
        self.assertEqual("warning: no such job: 'spam'\n",
                         result.output)
        self.assertTrue(os.path.exists(self.work_dir + '/jobs/spam.xml'))
        self.assertEqual(
            self.Jenkins.return_value.delete_job.call_args_list,
            [],
        )

    def test_delete_missing_config(self):
        with self.assertRaises(cexc.BadParameter):
            result = self.run_command('jobs delete --force jobs/foo.xml '
                                      'jobs/spam.xml', exit_code=2)
            self.assertIn('Error: Invalid value for "jobs": Path '
                          '"jobs/spam.xml" does not exist.', result.output)


class JobsUpdateCommandTest(base.JbutlerCommandTestCase):
    """Test the jbutler jobs command and sub-commands"""

    def test_update(self):
        result = self.run_command('jobs update jobs/foo.xml', exit_code=0)
        self.assertEqual('', result.output)
        self.assertEqual(
            [mock.call(base.FOO_JOB)],
            self.jobs['foo'].update_config.call_args_list,
        )

    def test_update_missing_config(self):
        with self.assertRaises(cexc.BadParameter):
            result = self.run_command('jobs update jobs/foo.xml '
                                      'jobs/spam.xml', exit_code=2)
            self.assertIn('Error: Invalid value for "jobs": Could not open '
                          'file: jobs/spam.xml: No such file or directory',
                          result.output)

    def test_update_missing_job(self):
        self.mkfile('jobs/spam.xml', contents=base.BAR_JOB)

        result = self.run_command('jobs update jobs/foo.xml jobs/spam.xml',
                                  exit_code=0)
        self.assertEqual("warning: no such job: 'spam'\n", result.output)
        self.jobs['foo'].update_config.assert_called_once_with(base.FOO_JOB)

    def test_update_multiple_jobs(self):
        result = self.run_command('jobs update jobs/foo.xml jobs/bar.xml',
                                  exit_code=0)
        self.assertEqual('', result.output)
        self.jobs['foo'].update_config.assert_called_once_with(base.FOO_JOB)
        self.jobs['bar'].update_config.assert_called_once_with(base.BAR_JOB)
