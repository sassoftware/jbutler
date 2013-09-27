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
import mock


from jbutler.jenkinsapi.job import Job
import jbutler

from jbutler_test import jbutlerhelp


FOO_JOB = """\
Contents of Foo job.
"""

BAR_JOB = """\
Contents of Bar Job.
"""

BAZ_JOB = """\
Contents of Baz Job.
"""

JBUTLER_RC = """\
password                  c2VjcmV0
server                    http://jenkins.example.com
ssl_verify                True
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

    def test_successful_config_show(self):
        self.mkfile('jbutlerrc', contents=JBUTLER_RC)

        out = self.runCommand('config', exitCode=0)
        expectedOut = 'password                  <password>\n' \
                      'server                    http://jenkins.example.com\n' \
                      'ssl_verify                True\n' \
                      'username                  test\n'

        self.assertEqual(out, expectedOut)

    def test_successful_config_show_exposed_password(self):
        self.mkfile('jbutlerrc', contents=JBUTLER_RC)

        out = self.runCommand('config --show-passwords', exitCode=0)
        expectedOut = 'password                  secret\n' \
                      'server                    http://jenkins.example.com\n' \
                      'ssl_verify                True\n' \
                      'username                  test\n'

        self.assertEqual(out, expectedOut)

    def test_successful_config_show_alt_config_file(self):
        self.mkfile('jbutlerrc_alt', contents=JBUTLER_RC)

        cmd = "config --config-file=%s/jbutlerrc_alt" % self.workDir
        out = self.runCommand(cmd, exitCode=0)
        expectedOut = 'password                  <password>\n' \
                      'server                    http://jenkins.example.com\n' \
                      'ssl_verify                True\n' \
                      'username                  test\n'

        self.assertEqual(out, expectedOut)
        
    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_successful_job_creation(self, _Jenkins):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        
        # mock an instance of Jenkins object that return mockJob
        mockJenkins = _Jenkins.return_value 
        mockJenkins.has_job.return_value = False
        mockJenkins.create_job.return_value = mockJob

        out = self.runCommand('jobs create', exitCode=0)
        self.assertEqual("", out)

        # verify JenkinsAPI asked to create job
        mockJenkins.create_job.assert_called_once_with(config=FOO_JOB,
                jobname='foo')

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_successful_job_creation_with_list(self, _Jenkins):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that returns mockJob
        mockJenkins = _Jenkins.return_value
        mockJenkins.has_job.return_value = False
        mockJenkins.create_job.return_value = mockJob

        out = self.runCommand('jobs create foo', exitCode=0)
        self.assertEqual("", out)

        # verify JenkinsAPI asked to create job
        mockJenkins.create_job.assert_called_once_with(config=FOO_JOB,
                jobname='foo')

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_successful_job_creation_with_list_missing_item(self, _Jenkins):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        mockJenkins = _Jenkins.return_value
        mockJenkins.has_job.return_value = False
        mockJenkins.create_job.return_value = mockJob

        out = self.runCommand('jobs create foo bar', exitCode=0)
        self.assertEqual(
            "These jobs were not found in the jobs directory: bar.xml\n",
            out)

        # verify JenkinsAPI asked to create job
        mockJenkins.create_job.assert_called_once_with(config=FOO_JOB,
                jobname='foo')

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_successful_job_retrieval(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        mockJenkins = _Jenkins.return_value
        mockJenkins.get_jobs.return_value = iter([('foo', mockJob)])

        out = self.runCommand('jobs retrieve', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs 
        mockJenkins.get_jobs.assert_called_once_with()

        self.assertEqual("", out)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)


    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_successful_job_retrieval_with_list(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        mockJenkins = _Jenkins.return_value
        mockJenkins.has_job.return_value = True
        mockJenkins.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve foo', exitCode=0)
        self.assertEqual("", out)

        # verify jbutler asks JenkinsAPI for job foo
        mockJenkins.has_job.assert_called_once_with('foo')
        mockJenkins.get_job.assert_called_once_with('foo')

        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_successful_job_retrieval_with_missing_item(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        mockJenkins = _Jenkins.return_value
        mockJenkins.has_job.side_effect = [True, False]
        mockJenkins.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve foo bar', exitCode=0)
        self.assertEqual(
            "Server does not have job 'bar'\n",
            out)

        # verify jbutler asks JenkinsAPI for both jobs
        mockJenkins.has_job.call_list = ['foo', 'bar']
        mockJenkins.get_job.assert_called_once_with('foo')

        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)
        self.assertFalse(os.path.exists(self.workDir + '/jobs/bar.xml'))

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_retrieval_filter_simple(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object for foo
        mockFooJob = mock.MagicMock(spec=Job)
        mockFooJob.name = 'foo'
        mockFooJob.get_config.return_value = FOO_JOB

        # create a mocked job object for bar
        mockBarJob = mock.MagicMock(spec=Job)
        mockBarJob.name = 'bar'
        mockBarJob.get_config.return_value = BAR_JOB

        # mock out Jenkins object
        mockJenkins = _Jenkins.return_value
        mockJenkins.get_jobs.return_value = \
            iter([('foo', mockFooJob), ('bar', mockBarJob)])

        out = self.runCommand('jobs retrieve --filter=foo', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs 
        mockJenkins.get_jobs.assert_called_once_with()

        self.assertEqual("", out)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)
        self.assertFalse(os.path.exists(self.workDir + '/jobs/bar.xml'))

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_retrieval_filter_glob(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJobFoo = mock.MagicMock(spec=Job)
        mockJobFoo.name = 'foo'
        mockJobFoo.get_config.return_value = FOO_JOB

        mockJobBar = mock.MagicMock(spec=Job)
        mockJobBar.name = 'bar'
        mockJobBar.get_config.return_value = "A bar job\n"

        # mock out Jenkins object
        mockJenkins = _Jenkins.return_value
        mockJenkins.get_jobs.return_value = iter([
            ('foo', mockJobFoo),
            ('bar', mockJobBar),
            ])

        out = self.runCommand('jobs retrieve --filter=f.*', exitCode=0)
        self.assertEqual("", out)

        # verify jbutler asked JenkinsAPI for jobs
        mockJenkins.get_jobs.assert_called_once_with()

        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    @mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                spec=jbutler.utils.jenkins_utils.Jenkins)
    def test_retrieval_filter_glob2(self, _Jenkins):
        self.mkdirs('jobs')

        # create a mocked job object for foo
        mockFooJob = mock.MagicMock(spec=Job)
        mockFooJob.name = 'foo'
        mockFooJob.get_config.return_value = FOO_JOB

        # create a mocked job object for bar
        mockBarJob = mock.MagicMock(spec=Job)
        mockBarJob.name = 'bar'
        mockBarJob.get_config.return_value = BAR_JOB

        # create a mocked job object for baz
        mockBazJob = mock.MagicMock(spec=Job)
        mockBazJob.name = 'baz'
        mockBazJob.get_config.return_value = BAZ_JOB

        # mock out Jenkins object
        mockJenkins = _Jenkins.return_value
        mockJenkins.get_jobs.return_value = \
            iter([('foo', mockFooJob), ('bar', mockBarJob), ('baz', mockBazJob)])

        out = self.runCommand('jobs retrieve --filter=\'ba*\'', exitCode=0)
        
        # verify jbutler asks JenkinsAPI for jobs 
        mockJenkins.get_jobs.assert_called_once_with()

        self.assertEqual("", out)
        self.assertFalse(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertTrue(os.path.exists(self.workDir + '/jobs/bar.xml'))
        self.assertEqual(open(self.workDir + '/jobs/bar.xml').read(), BAR_JOB)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/baz.xml'))
        self.assertEqual(open(self.workDir + '/jobs/baz.xml').read(), BAZ_JOB)

