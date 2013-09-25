#!/usr/bin/python
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


import os

from jenkinsapi import jenkins
import mock

from jbutler_test import jbutlerhelp


FOO_JOB = """\
Just a file
"""

JBUTLER_RC = """\
password                  c2VjcmV0
server                    http://jenkins.example.com
username                  test
"""

class JobsCommandTest(jbutlerhelp.JButlerCommandTest):
    """
    Test the jbutler jobs command and sub-commands
    """

    def test_no_jobs_dir(self):
        out = self.runCommand('jobs create', exitCode=1)
        self.assertEqual(out, 'error: no jobs directory found in %s\n' %
                         self.workDir)

    def test_empty_jobs_dir(self):
        self.mkdirs('jobs')

        out = self.runCommand('jobs create', exitCode=0)
        self.assertEqual(out, 'No jobs found\n')

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successful_config_show(self, _Jenkins):
        self.mkfile('jbutlerrc', contents=JBUTLER_RC)

        out = self.runCommand('config', exitCode=0)
        expectedOut = 'password                  <password>\n' \
                      'server                    http://jenkins.example.com\n' \
                      'username                  test\n'

        self.assertEqual(out, expectedOut)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successfull_job_creation(self, _Jenkins):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=jenkins.Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        mockJenkins = mock.MagicMock(spec=jenkins.Jenkins)
        mockJenkins.create_job.return_value = mockJob
        _Jenkins.return_value = mockJenkins

        out = self.runCommand('jobs create', exitCode=0)
        self.assertEqual("", out)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successfull_job_creation_with_list(self, _Jenkins):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=jenkins.Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        mockJenkins = mock.MagicMock(spec=jenkins.Jenkins)
        mockJenkins.create_job.return_value = mockJob
        _Jenkins.return_value = mockJenkins

        out = self.runCommand('jobs create foo', exitCode=0)
        self.assertEqual("", out)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successfull_job_creation_with_list_missing_item(self, _Jenkins):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=jenkins.Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        mockJenkins = mock.MagicMock(spec=jenkins.Jenkins)
        mockJenkins.create_job.return_value = mockJob
        _Jenkins.return_value = mockJenkins

        out = self.runCommand('jobs create foo bar', exitCode=0)
        self.assertEqual(
            "These jobs were not found in the jobs directory: bar.xml\n",
            out)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successfull_job_retrieval(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=jenkins.Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        _Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)
        _Jenkins.return_value.get_jobs.return_value = iter([('foo', mockJob)])

        out = self.runCommand('jobs retrieve', exitCode=0)
        self.assertEqual("", out)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successfull_job_retrieval_with_list(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=jenkins.Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        _Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)
        _Jenkins.return_value.has_job.return_value = True
        _Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve foo', exitCode=0)

        self.assertEqual("", out)
        _Jenkins.return_value.has_job.assert_called_once_with('foo')
        _Jenkins.return_value.get_job.assert_called_once_with('foo')
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_successfull_job_retrieval_with_missing_item(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=jenkins.Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        _Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)
        _Jenkins.return_value.has_job.side_effect = (True, False)
        _Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve foo bar', exitCode=0)

        self.assertEqual(
            "Server does not have job 'bar'\n",
            out)
        _Jenkins.return_value.has_job.call_list = ['foo', 'bar']
        _Jenkins.return_value.get_job.assert_called_once_with('foo')
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins')
    def test_retrieval_filter(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJobFoo = mock.MagicMock(spec=jenkins.Job)
        mockJobFoo.name = 'foo'
        mockJobFoo.get_config.return_value = FOO_JOB

        mockJobBar = mock.MagicMock(spec=jenkins.Job)
        mockJobBar.name = 'bar'
        mockJobBar.get_config.return_value = "A bar job\n"

        # mock out Jenkins object
        _Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)
        _Jenkins.return_value.get_jobs.return_value = iter([
            ('foo', mockJobFoo),
            ('bar', mockJobBar),
            ])

        out = self.runCommand('jobs retrieve --filter=f.*', exitCode=0)
        self.assertEqual("", out)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)
