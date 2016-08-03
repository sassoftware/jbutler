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
try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import os
import shutil
import tempfile

from click.testing import CliRunner
from jbutler.commands import base
import jenkinsapi


class JbutlerTestCase(unittest.TestCase):
    test_dir_name = 'jbutler-test-'

    def setUp(self):
        self.work_dir = tempfile.mkdtemp(prefix=self.test_dir_name)

        orig_dir = os.getcwd()
        os.chdir(self.work_dir)

        self.addCleanup(shutil.rmtree, self.work_dir)
        self.addCleanup(os.chdir, orig_dir)

    def mkdirs(self, path):
        if not path.startswith(os.sep):
            # Relative paths are relative to self.work_dir
            path = os.path.join(self.work_dir, path)
        os.makedirs(path)
        return path

    def mkfile(self, path, contents=None):
        if not path.startswith(os.sep):
            # Relative paths are relative to self.work_dir
            path = os.path.join(self.work_dir, path)
        if contents:
            with open(path, 'w') as fh:
                fh.write(contents)
        return path


class JbutlerCommandTestCase(JbutlerTestCase):
    def setUp(self):
        super(JbutlerCommandTestCase, self).setUp()
        self.mkfile('jbutlerrc', contents=JBUTLER_RC)

        self.mkdirs('jobs')
        self.mkfile('jobs/foo.xml', contents=FOO_JOB)
        self.mkfile('jobs/bar.xml', contents=BAR_JOB)
        self.mkfile('jobs/baz.xml', contents=BAZ_JOB)

        Jenkins_patcher = mock.patch('jbutler.utils.jenkins_utils.Jenkins',
                                     spec=jenkinsapi.jenkins.Jenkins)
        self.Jenkins = Jenkins_patcher.start()
        self.addCleanup(Jenkins_patcher.stop)

        _foo = mock.MagicMock(spec=jenkinsapi.job.Job)
        _foo.name = 'foo'
        _foo.get_config.return_value = FOO_JOB

        _bar = mock.MagicMock(spec=jenkinsapi.job.Job)
        _bar.name = 'bar'
        _bar.get_config.return_value = BAR_JOB

        _baz = mock.MagicMock(spec=jenkinsapi.job.Job)
        _baz.name = 'baz'
        _baz.get_config.return_value = BAZ_JOB

        self.jobs = {'foo': _foo,
                     'bar': _bar,
                     'baz': _baz,
                     }

        def has_job(name):
            return name in self.jobs

        def get_job(name):
            return self.jobs[name]

        self.Jenkins.return_value.has_job.side_effect = has_job
        self.Jenkins.return_value.get_job.side_effect = get_job
        self.Jenkins.return_value.get_jobs_info.return_value = iter([
            ('foourl', 'foo'),
            ('barurl', 'bar'),
            ('bazurl', 'baz'),
        ])

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()

    def run_command(self, args=None, exit_code=None, **kwargs):
        cmd = ['--skip-default-config', '--config-file', './jbutlerrc']
        if isinstance(args, str):
            cmd.extend(args.split(' '))
        elif isinstance(args, (list, tuple, set)):
            cmd.extend(args)
        else:
            raise TypeError("invalid type for args: '%s'" % type(args))
        result = self.runner.invoke(base.jbutler, cmd, standalone_mode=False,
                                    **kwargs)
        if result.exception is not None:
            raise result.exception

        if exit_code is not None:
            self.assertEqual(exit_code, result.exit_code)
        return result


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
[jbutler]
password = secret
server = http://jenkins.example.com
username = test
"""
