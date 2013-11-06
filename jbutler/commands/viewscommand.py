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
import sys

from conary.lib import options

from .. import errors
from ..lib import command
from ..utils import jenkins_utils


class ViewCommand(command.CommandWithSubCommands):
    """
    View comand for working with jenkins views
    """
    help = 'Create/Retrieve jenkins views'
    commands = ['views']


class ViewSubCommand(command.BaseCommand):
    paramHelp = '[view]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        argDef['project'] = (options.OPT_PARAM, 'Path to project directory,'
                             ' defaults to current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, self.viewList = self.requireParameters(args, allowExtra=True)
        self.projectDir = argSet.pop('project', os.getcwd())
        self.projectDir = os.path.abspath(self.projectDir)
        self.viewConfig = os.path.join(self.projectDir, 'views.yml')

        # verify viewsDir exists
        if not (os.path.exists(self.viewConfig)
                and os.path.isfile(self.viewConfig)):
            raise errors.CommandError(
                'no views configuration found at %s' % (self.projectDir)
                )


class ViewCreateCommand(ViewSubCommand):
    help = 'Create a jenkins view from config file'
    commands = ['create']

    def runCommand(self, cfg, argSet, args, **kwargs):
        ViewSubCommand.runCommand(self, cfg, argSet, args, **kwargs)

        server = jenkins_utils.server_factory(cfg)
        with open(self.viewConfig) as fh:
            server.views.deserialize(fh.read(), self.viewList)
ViewCommand.registerSubCommand('create', ViewCreateCommand)


class ViewDeleteCommand(ViewSubCommand):
    help = 'Delete view and all sub-views'
    command = ['delete']
    paramHelp = '<view>+'

    def addLocalParameters(self, argDef):
        ViewSubCommand.addLocalParameters(self, argDef)
        argDef['force'] = (options.NO_PARAM, 'Also delete view from local'
                           ' config file')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, self.viewList = self.requireParameters(
            args, expected='view', appendExtra=True)
        self.projectDir = argSet.pop('project', os.getcwd())
        self.projectDir = os.path.abspath(self.projectDir)
        self.viewConfig = os.path.join(self.projectDir, 'views.yml')

        # verify viewsDir exists
        if not (os.path.exists(self.viewConfig)
                and os.path.isfile(self.viewConfig)):
            raise errors.CommandError(
                'no views configuration found at %s' % (self.projectDir)
                )
        force = argSet.pop('force', False)

        server = jenkins_utils.server_factory(cfg)

        created_views = None
        for viewName in self.viewList:
            if server.has_view(viewName):
                created_views = server.delete_view(viewName)
            else:
                sys.stdout.write(
                    "warning: no such view found on server: '%s'\n" % viewName)

        if force and created_views:
            with open(self.viewConfig, 'w') as fh:
                fh.write(created_views.serialize())
ViewCommand.registerSubCommand('delete', ViewDeleteCommand)


class ViewRetrieveComand(ViewSubCommand):
    help = 'Retrieve view, and all sub-views from jenkins server'
    commands = ['retrieve']

    def runCommand(self, cfg, argSet, args, **kwargs):
        ViewSubCommand.runCommand(self, cfg, argSet, args, **kwargs)

        server = jenkins_utils.server_factory(cfg)
        retrieved_views = server.views.serialize(self.viewList)
        with open(self.viewConfig, 'w') as fh:
            fh.write(retrieved_views)
ViewCommand.registerSubCommand('retrieve', ViewRetrieveComand)


class ViewUpdateCommand(ViewSubCommand):
    help = 'Update existing view with new configuration'
    commands = ['update']

    def runCommand(self, cfg, argSet, args, **kwargs):
        ViewSubCommand.runCommand(self, cfg, argSet, args, **kwargs)
        server = jenkins_utils.server_factory(cfg)
        with open(self.viewConfig) as fh:
            server.views.deserialize(fh.read(), self.viewList, update=True)
ViewCommand.registerSubCommand('update', ViewUpdateCommand)
