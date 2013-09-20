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

from jbutler.lib import jobs

from jbutler_test import jbutlerhelp


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
        self.assertEqual(out, 'Created: []\n')
