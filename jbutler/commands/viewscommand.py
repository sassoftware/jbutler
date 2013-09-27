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
views command
"""
import os

from conary.lib import options

from jbutler import errors
from jbutler.lib import command, views


class ViewCommand(command.CommandWithSubCommands):
    """
    View comand for working with jenkins views
    """
    help = 'Create/Retrieve jenkins views'
    commands = ['views']


class ViewCreateCommand(command.BaseCommand):
    help = 'Create a jenkins view from config file'
    commands = ['create']
    paramHelp = '[view name]*'
    requireConfig = True

    def addParameters(self, argDef):
        super(ViewCreateCommand, self).addParameters(argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project directory,'
                             ' defaults to current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, viewsList = self.requireParameters(args, allowExtra=True)
        if not viewsList:
            viewsList = None

        projectDir = argSet.pop('project', os.getcwd())
        projectDir = os.path.abspath(projectDir)
        viewsFile = os.path.join(projectDir, 'views.yml')

        # verify viewsDir exists
        if not (os.path.exists(viewsFile) and os.path.isfile(viewsFile)):
            raise errors.CommandError(
                'no views configuration found at %s' % (projectDir)
                )

        views.createViews(cfg, viewsList, viewsFile)

ViewCommand.registerSubCommand('create', ViewCreateCommand)


class ViewRetrieveComand(command.BaseCommand):
    help = 'Retrieve view, and all sub-views from jenkins server'
    commands = ['retrieve']
    paramHelp = '[view name]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        super(ViewRetrieveComand, self).addLocalParameters(argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, viewsList = self.requireParameters(args, allowExtra=True)
        if not viewsList:
            viewsList = None

        projectDir = argSet.pop('project', os.getcwd())
        projectDir = os.path.abspath(projectDir)
        viewsFile = os.path.join(projectDir, 'views.yml')

        views.retrieveViews(cfg, viewsList, viewsFile)

ViewCommand.registerSubCommand('retrieve', ViewRetrieveComand)
