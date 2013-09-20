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

"""
job command
"""
import os

from conary.lib import options

from .. import errors
from ..lib import command, jobs


class JobCommand(command.CommandWithSubCommands):
    """
    Job command for creating/changing jenkins jobs
    """
    help = 'Create/Edit jenkins jobs'
    commands = ['jobs']


class JobCreateCommand(command.BaseCommand):
    help = 'Create a jenkins job'
    command = ['create']
    paramHelp = '[jobs]...'
    requireConfig = True

    def addParameters(self, argDef):
        super(JobCreateCommand, self).addParameters(argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        args = self.requireParameters(args, appendExtra=True)

        projectDir = argSet.pop('project', os.getcwd())
        projectDir = os.path.abspath(projectDir)
        jobsDir = os.path.join(projectDir, 'jobs')

        # verify jobsDir exist
        if not (os.path.exists(jobsDir) and os.path.isdir(jobsDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % (projectDir)
                )

        results = jobs.createJobs(cfg, args, jobsDir)
        print('Created: %s' % results)

JobCommand.registerSubCommand('create', JobCreateCommand)
