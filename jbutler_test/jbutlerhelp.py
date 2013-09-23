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


import StringIO
import base64
import os
import shlex
import sys

from conary.lib import util

from jbutler import butlercfg
from jbutler.lib import mainhandler
from testrunner import testcase
from testutils import mock
import testsuite


# Bootstrap the testsuite
testsuite.setup()


class TestCase(testcase.TestCaseWithWorkDir):
    testDirName = 'jbutler-test-'

    def setUp(self):
        testcase.TestCaseWithWorkDir.setUp(self)
        self.rootDir = self.workDir

    def mkdirs(self, path):
        if not path.startswith(os.sep):
            # Relative paths are relative to self.rootDir
            path = os.path.join(self.rootDir, path)
        util.mkdirChain(path)
        return path

    def mkfile(self, path, contents=None):
        if not path.startswith(os.sep):
            # Relative paths are relative to self.rootDir
            path = os.path.join(self.rootDir, path)
        if contents:
            with open(path, 'w') as fh:
                fh.write(contents or '')
        return path


class JButlerHelper(TestCase):
    """
    Base class for all jbutler tests
    """

    def setUp(self):
        super(JButlerHelper, self).setUp()
        self.cfg = butlercfg.ButlerConfiguration(
            readConfigFiles=False,
            )
        self.cfg.username = 'test'
        self.cfg.password = base64.b64encode('secret')
        self.cfg.server = 'http://jenkins.example.com'


class JButlerCommandTest(JButlerHelper):
    """
    Test for exercising jbutler commands
    """

    def setUp(self):
        super(JButlerCommandTest, self).setUp()
        mock.mock(butlercfg.ButlerConfiguration, 'isComplete', True)
        os.chdir(self.workDir)
        self.cfg.writeToFile(self.workDir + '/jbutlerrc')

    def runCommand(self, commandString, exitCode=0, subDir=None, stdin=''):
        curDir = None
        if subDir:
            curDir = os.getcwd()
            os.chdir(subDir)

        # if stdin specified, then mockout sys.stdin
        if len(stdin):
            stdin, sys.stdin = sys.stdin, StringIO.StringIO(stdin)

        try:
            cmd = 'jbutler --config-file=%s --skip-default-config %s'
            cmd %= (self.workDir + '/jbutlerrc', commandString)
            argv = shlex.split(cmd)

            try:
                rc, out = self.captureOutput(mainhandler.main, argv)
            except SystemExit as err:
                rc = err.code
                out = ''
            if exitCode != rc:
                raise RuntimeError(
                    'Expected error code %s, got error code %s. Output:\n%s' %
                    (exitCode, rc, out)
                    )
            return out
        finally:
            if curDir:
                os.chdir(curDir)
            sys.stdin = stdin
