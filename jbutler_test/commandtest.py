#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
import os
import mock


from jbutler.jenkinsapi.job import Job
import jbutler

from jbutler_test import jbutlerhelp


FOO_JOB = """\
<?xml version='1.0' encoding='UTF-8'?>
<project>
    <foo>Contents of Foo job.</foo>
</project>
"""

BAR_JOB = """\
<?xml version='1.0' encoding='UTF-8'?>
<project>
    <bar>Contents of Bar Job.</bar>
</project>
"""

BAZ_JOB = """\
<?xml version='1.0' encoding='UTF-8'?>
<project>
    <baz>Contents of Baz Job.</baz>
</project>
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
        expectedOut = (
            'jobDir                    jobs\n'
            'password                  <password>\n'
            'server                    http://jenkins.example.com\n'
            'ssl_verify                True\n'
            'templateDir               templates\n'
            'username                  test\n'
            )

        self.assertEqual(out, expectedOut)

    def test_successful_config_show_exposed_password(self):
        self.mkfile('jbutlerrc', contents=JBUTLER_RC)

        out = self.runCommand('config --show-passwords', exitCode=0)
        expectedOut = (
            'jobDir                    jobs\n'
            'password                  secret\n'
            'server                    http://jenkins.example.com\n'
            'ssl_verify                True\n'
            'templateDir               templates\n'
            'username                  test\n'
            )

        self.assertEqual(out, expectedOut)

    def test_successful_config_show_alt_config_file(self):
        self.mkfile('jbutlerrc_alt', contents=JBUTLER_RC)

        cmd = "config --config-file=%s/jbutlerrc_alt" % self.workDir
        out = self.runCommand(cmd, exitCode=0)
        expectedOut = (
            'jobDir                    jobs\n'
            'password                  <password>\n'
            'server                    http://jenkins.example.com\n'
            'ssl_verify                True\n'
            'templateDir               templates\n'
            'username                  test\n'
            )

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
        mockJenkins.get_jobs_info.return_value = iter([('url', 'foo')])
        mockJenkins.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs
        mockJenkins.get_job.assert_called_once_with('foo')

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
        mockJenkins.get_jobs_info.return_value = \
            iter([('foourl', 'foo'), ('barurl', 'bar')])
        mockJenkins.get_job.side_effect = [mockFooJob, mockBarJob]

        out = self.runCommand('jobs retrieve --filter=foo', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs
        mockJenkins.get_job.assert_called_once_with('foo')
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
        mockJenkins.get_jobs_info.return_value = iter([
            ('foourl', 'foo'),
            ('barurl', 'bar'),
            ])
        mockJenkins.get_job.side_effect = [mockJobFoo]

        out = self.runCommand('jobs retrieve --filter=f.*', exitCode=0)
        self.assertEqual("", out)

        # verify jbutler asked JenkinsAPI for jobs
        mockJenkins.get_job.assert_called_once_with('foo')

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
        mockJenkins.get_jobs_info.return_value = \
            iter([('foourl', 'foo'), ('barurl', 'bar'), ('bazurl', 'baz')])
        mockJenkins.get_job.side_effect = [mockBarJob, mockBazJob]

        out = self.runCommand('jobs retrieve --filter=\'ba*\'', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertEqual(
            mockJenkins.get_job.call_args_list,
            [mock.call('bar'), mock.call('baz')])

        self.assertEqual("", out)
        self.assertFalse(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertTrue(os.path.exists(self.workDir + '/jobs/bar.xml'))
        self.assertEqual(open(self.workDir + '/jobs/bar.xml').read(), BAR_JOB)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/baz.xml'))
        self.assertEqual(open(self.workDir + '/jobs/baz.xml').read(), BAZ_JOB)
