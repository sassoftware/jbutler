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
    <disabled>false</disabled>
    <foo>Contents of Foo job.</foo>
</project>
"""

BAR_JOB = """\
<?xml version='1.0' encoding='UTF-8'?>
<project>
    <disabled>false</disabled>
    <bar>Contents of Bar Job.</bar>
</project>
"""

BAZ_JOB = """\
<?xml version='1.0' encoding='UTF-8'?>
<project>
    <disabled>false</disabled>
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

    def setUp(self):
        jbutlerhelp.JButlerCommandTest.setUp(self)

        self.Jenkins_patcher = mock.patch(
            'jbutler.utils.jenkins_utils.Jenkins',
            spec=jbutler.utils.jenkins_utils.Jenkins)
        self.Jenkins = self.Jenkins_patcher.start()

    def tearDown(self):
        jbutlerhelp.JButlerCommandTest.tearDown(self)

        self.Jenkins_patcher.stop()

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

    def test_create_no_jobs(self):
        out = self.runCommand('jobs create', exitCode=1)
        self.assertEqual(
            out, "error: 'create' missing 1 command parameter(s): file\n")

    def test_successful_job_creation(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = False
        self.Jenkins.return_value.create_job.return_value = mockJob

        out = self.runCommand('jobs create jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')

        # verify JenkinsAPI asked to create job
        self.Jenkins.return_value.create_job.assert_called_once_with(
            config=FOO_JOB, jobname='foo')

    def test_successful_job_creation_with_list(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)
        self.mkfile('jobs/bar.xml', contents=BAR_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that returns mockJob
        self.Jenkins.return_value.has_job.return_value = False
        self.Jenkins.return_value.create_job.return_value = mockJob

        out = self.runCommand('jobs create jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')

        # verify JenkinsAPI asked to create job
        self.Jenkins.return_value.create_job.assert_called_once_with(
            config=FOO_JOB, jobname='foo')

    def test_successful_job_creation_with_list_missing_item(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = False
        self.Jenkins.return_value.create_job.return_value = mockJob

        out = self.runCommand(
            'jobs create jobs/foo.xml jobs/bar.xml', exitCode=1)
        self.assertEqual(
            "error: [Errno 2] No such file or directory: 'jobs/bar.xml'\n",
            out)

        # verify JenkinsAPI asked to create job
        self.Jenkins.return_value.create_job.assert_called_once_with(
            config=FOO_JOB, jobname='foo')

    def test_successful_job_retrieval(self):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        self.Jenkins.return_value.get_jobs_info.return_value = iter(
            [('url', 'foo')])
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs
        self.Jenkins.return_value.get_job.assert_called_once_with('foo')

        self.assertEqual(out, '')
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    def test_successful_job_retrieval_with_list(self):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve foo', exitCode=0)
        self.assertEqual(out, '')

        # verify jbutler asks JenkinsAPI for job foo
        self.Jenkins.return_value.has_job.assert_called_once_with('foo')
        self.Jenkins.return_value.get_job.assert_called_once_with('foo')

        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    def test_successful_job_retrieval_with_missing_item(self):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.get_config.return_value = FOO_JOB

        # mock out Jenkins object
        self.Jenkins.return_value.has_job.side_effect = [True, False]
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs retrieve foo bar', exitCode=0)
        self.assertEqual(out, "warning: server does not have job 'bar'\n")

        # verify jbutler asks JenkinsAPI for both jobs
        self.Jenkins.return_value.has_job.call_list = ['foo', 'bar']
        self.Jenkins.return_value.get_job.assert_called_once_with('foo')

        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)
        self.assertFalse(os.path.exists(self.workDir + '/jobs/bar.xml'))

    def test_retrieval_filter_simple(self):
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
        self.Jenkins.return_value.get_jobs_info.return_value = \
            iter([('foourl', 'foo'), ('barurl', 'bar')])
        self.Jenkins.return_value.get_job.side_effect = [
            mockFooJob, mockBarJob]

        out = self.runCommand('jobs retrieve --filter=foo', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs
        self.Jenkins.return_value.get_job.assert_called_once_with('foo')
        self.assertEqual(out, '')
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)
        self.assertFalse(os.path.exists(self.workDir + '/jobs/bar.xml'))

    def test_retrieval_filter_glob(self):
        self.mkdirs('jobs')

        # create a mocked job object
        mockJobFoo = mock.MagicMock(spec=Job)
        mockJobFoo.name = 'foo'
        mockJobFoo.get_config.return_value = FOO_JOB

        mockJobBar = mock.MagicMock(spec=Job)
        mockJobBar.name = 'bar'
        mockJobBar.get_config.return_value = "A bar job\n"

        # mock out Jenkins object
        self.Jenkins.return_value.get_jobs_info.return_value = iter([
            ('foourl', 'foo'),
            ('barurl', 'bar'),
            ])
        self.Jenkins.return_value.get_job.side_effect = [mockJobFoo]

        out = self.runCommand('jobs retrieve --filter=f.*', exitCode=0)
        self.assertEqual(out, '')

        # verify jbutler asked JenkinsAPI for jobs
        self.Jenkins.return_value.get_job.assert_called_once_with('foo')

        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(open(self.workDir + '/jobs/foo.xml').read(), FOO_JOB)

    def test_retrieval_filter_glob2(self):
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
        self.Jenkins.return_value.get_jobs_info.return_value = \
            iter([('foourl', 'foo'), ('barurl', 'bar'), ('bazurl', 'baz')])
        self.Jenkins.return_value.get_job.side_effect = [
            mockBarJob, mockBazJob]

        out = self.runCommand('jobs retrieve --filter=\'ba*\'', exitCode=0)

        # verify jbutler asks JenkinsAPI for jobs
        self.assertEqual(
            self.Jenkins.return_value.get_job.call_args_list,
            [mock.call('bar'), mock.call('baz')])

        self.assertEqual(out, '')
        self.assertFalse(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertTrue(os.path.exists(self.workDir + '/jobs/bar.xml'))
        self.assertEqual(open(self.workDir + '/jobs/bar.xml').read(), BAR_JOB)
        self.assertTrue(os.path.exists(self.workDir + '/jobs/baz.xml'))
        self.assertEqual(open(self.workDir + '/jobs/baz.xml').read(), BAZ_JOB)

    def test_disable_no_jobs(self):
        out = self.runCommand('jobs disable', exitCode=1)
        self.assertEqual(
            out, "error: 'disable' missing 1 command parameter(s): file\n")

    def test_disable(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs disable jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(
            '<disabled>false</disabled>' in
            open(self.workDir + '/jobs/foo.xml').read()
            )
        mockJob.disable.assert_called_once_with()

    def test_disable_force(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs disable --force jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(
            '<disabled>true</disabled>' in
            open(self.workDir + '/jobs/foo.xml').read()
            )
        mockJob.disable.assert_called_once_with()

    def test_enable_no_jobs(self):
        out = self.runCommand('jobs enable', exitCode=1)
        self.assertEqual(
            out, "error: 'enable' missing 1 command parameter(s): file\n")

    def test_enable(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.is_enabled.return_value = False

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs enable jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(
            '<disabled>false</disabled>' in
            open(self.workDir + '/jobs/foo.xml').read()
            )
        mockJob.enable.assert_called_once_with()

    def test_enable_disabled_job(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB.replace('false', 'true'))

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.is_enabled.return_value = False

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs enable jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(
            '<disabled>true</disabled>' in
            open(self.workDir + '/jobs/foo.xml').read()
            )
        self.assertEqual(mockJob.enable.call_args_list, [])

    def test_enable_force(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB.replace('false', 'true'))

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.is_enabled.return_value = False

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs enable --force jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(
            '<disabled>false</disabled>' in
            open(self.workDir + '/jobs/foo.xml').read()
            )
        mockJob.enable.assert_called_once_with()

    def test_enable_force_enabled_job(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB.replace('false', 'true'))

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'
        mockJob.is_enabled.return_value = True

        # mock an instance of Jenkins object that return mockJob
        self.Jenkins.return_value.has_job.return_value = True
        self.Jenkins.return_value.get_job.return_value = mockJob

        out = self.runCommand('jobs enable --force jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(
            '<disabled>false</disabled>' in
            open(self.workDir + '/jobs/foo.xml').read()
            )
        self.assertEqual(mockJob.enable.call_args_list, [])

    def test_delete_no_jobs(self):
        out = self.runCommand('jobs delete', exitCode=1)
        self.assertEqual(
            out, "error: 'delete' missing 1 command parameter(s): file\n")

    def test_delete(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        self.Jenkins.return_value.has_job.return_value = True

        out = self.runCommand('jobs delete jobs/foo.xml', exitCode=0)
        self.assertEqual(out, '')
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(
            self.Jenkins.return_value.delete_job.call_args_list,
            [mock.call('foo')],
            )

    def test_delete_missing_job(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        self.Jenkins.return_value.has_job.return_value = False

        out = self.runCommand('jobs delete jobs/foo.xml', exitCode=0)
        self.assertEqual(out, "warning: job does not exist on server: 'foo'\n")
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(
            self.Jenkins.return_value.delete_job.call_args_list,
            [],
            )

    def test_delete_missing_config(self):
        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)

        # create a job object
        mockJob = mock.MagicMock(spec=Job)
        mockJob.name = 'foo'

        self.Jenkins.return_value.has_job.return_value = True

        out = self.runCommand(
            'jobs delete jobs/foo.xml jobs/bar.xml', exitCode=1)
        self.assertEqual(
            out, "error: [Errno 2]: No such file or directory:"
            " 'jobs/bar.xml'\n")
        self.assertTrue(os.path.exists(self.workDir + '/jobs/foo.xml'))
        self.assertEqual(
            self.Jenkins.return_value.delete_job.call_args_list,
            [mock.call('foo')],
            )
