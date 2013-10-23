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
import re

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
    paramHelp = '[JOB]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, jobList = self.requireParameters(args, allowExtra=True)
        if not jobList:
            jobList = None

        projectDir = argSet.pop('project', os.getcwd())
        projectDir = os.path.abspath(projectDir)
        jobDir = os.path.join(projectDir, cfg.jobDir)

        # verify jobDir exist
        if not (os.path.exists(jobDir) and os.path.isdir(jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % (projectDir)
                )

        jobs.createJobs(cfg, jobList, jobDir)
JobCommand.registerSubCommand('create', JobCreateCommand)


class JobRetrieveCommand(command.BaseCommand):
    help = 'Retrieve a jenkins job'
    command = ['retrieve']
    paramHelp = '[JOB]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')
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


class JobDisableCommand(command.BaseCommand):
    help = 'Disable a jenkins job'
    commands = ['disable', 'off']
    paramHelp = '[JOB]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')
        argDef['filter'] = (options.OPT_PARAM, 'Filter to apply to jobs')
        argDef['force'] = (options.NO_PARAM, 'Force update of local config')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, jobList = self.requireParameters(args, allowExtra=True)
        if not jobList:
            jobList = None

        projectDir = argSet.pop('project', os.getcwd())
        jobFilter = argSet.pop('filter', None)
        force = argSet.pop('force', False)

        projectDir = os.path.abspath(projectDir)
        jobDir = os.path.join(projectDir, cfg.jobDir)

        # verify jobDir exist
        if not (os.path.exists(jobDir) and os.path.isdir(jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % (projectDir)
                )

        jobs.disableJobs(cfg, jobList, jobDir, jobFilter, force)
JobCommand.registerSubCommand('disable', JobDisableCommand)


class JobEnableCommand(command.BaseCommand):
    help = 'Disable a jenkins job'
    commands = ['enable', 'on']
    paramHelp = '[JOB]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')
        argDef['filter'] = (options.OPT_PARAM, 'Filter to apply to jobs')
        argDef['force'] = (options.NO_PARAM, 'Force update of local config')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, jobList = self.requireParameters(args, allowExtra=True)
        if not jobList:
            jobList = None

        projectDir = argSet.pop('project', os.getcwd())
        jobFilter = argSet.pop('filter', None)
        force = argSet.pop('force', False)

        projectDir = os.path.abspath(projectDir)
        jobDir = os.path.join(projectDir, cfg.jobDir)

        # verify jobDir exist
        if not (os.path.exists(jobDir) and os.path.isdir(jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % (projectDir)
                )

        jobs.enableJobs(cfg, jobList, jobDir, jobFilter, force)
JobCommand.registerSubCommand('enable', JobEnableCommand)
