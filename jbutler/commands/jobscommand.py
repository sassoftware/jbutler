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


class JobSubCommand(command.BaseCommand):
    paramHelp = '<file>+'
    requireConfig = True

    def addLocalParameters(self, argDef):
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, self.jobList = self.requireParameters(
            args, expected='file', appendExtra=True)


class JobCreateCommand(JobSubCommand):
    help = 'Create a jenkins job'
    command = ['create']

    def runCommand(self, cfg, argSet, args, **kwargs):
        JobSubCommand.runCommand(self, cfg, argSet, args, **kwargs)
        jobs.createJobs(cfg, self.jobList)
JobCommand.registerSubCommand('create', JobCreateCommand)


class JobRetrieveCommand(JobSubCommand):
    help = 'Retrieve a jenkins job'
    command = ['retrieve']
    paramHelp = '[JOB]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        JobSubCommand.addLocalParameters(self, argDef)
        argDef['filter'] = (options.OPT_PARAM, 'Filter to apply to jobs')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, jobList = self.requireParameters(args, allowExtra=True)
        if not jobList:
            jobList = None

        projectDir = argSet.pop('project', os.getcwd())
        jobFilter = argSet.pop('filter', None)

        projectDir = os.path.abspath(projectDir)
        jobDir = os.path.join(projectDir, cfg.jobDir)

        # verify jobDir exist
        if not (os.path.exists(jobDir) and os.path.isdir(jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % (projectDir)
                )

        jobs.retrieveJobs(cfg, jobList, jobDir, jobFilter)
JobCommand.registerSubCommand('retrieve', JobRetrieveCommand)


class JobDisableCommand(JobSubCommand):
    help = 'Disable a jenkins job'
    commands = ['disable', 'off']

    def addLocalParameters(self, argDef):
        JobSubCommand.addLocalParameters(self, argDef)
        argDef['force'] = (options.NO_PARAM, 'Force update of local config')

    def runCommand(self, cfg, argSet, args, **kwargs):
        JobSubCommand.runCommand(self, cfg, argSet, args, **kwargs)

        force = argSet.pop('force', False)

        jobs.disableJobs(cfg, self.jobList, force)
JobCommand.registerSubCommand('disable', JobDisableCommand)


class JobEnableCommand(JobSubCommand):
    help = 'Disable a jenkins job'
    commands = ['enable', 'on']

    def addLocalParameters(self, argDef):
        JobSubCommand.addLocalParameters(self, argDef)
        argDef['force'] = (options.NO_PARAM, 'Force update of local config')

    def runCommand(self, cfg, argSet, args, **kwargs):
        JobSubCommand.runCommand(self, cfg, argSet, args, **kwargs)
        force = argSet.pop('force', False)
        jobs.enableJobs(cfg, self.jobList, force)
JobCommand.registerSubCommand('enable', JobEnableCommand)


class JobDeleteCommand(JobSubCommand):
    help = 'Delete a jenkins job'
    commands = ['delete']

    def addLocalParameters(self, argDef):
        JobSubCommand.addLocalParameters(self, argDef)
        argDef['force'] = (options.NO_PARAM, 'Also delete local config file')

    def runCommand(self, cfg, argSet, args, **kwargs):
        JobSubCommand.runCommand(self, cfg, argSet, args, **kwargs)
        force = argSet.pop('force', False)
        jobs.deleteJobs(cfg, self.jobList, force)
JobCommand.registerSubCommand('delete', JobDeleteCommand)


class JobUpdateCommand(JobSubCommand):
    help = 'Update a jenkins job'
    commands = ['update']

    def runCommand(self, cfg, argSet, args, **kwargs):
        JobSubCommand.runCommand(self, cfg, argSet, args, **kwargs)
        jobs.updateJobs(cfg, self.jobList)
JobCommand.registerSubCommand('update', JobUpdateCommand)
