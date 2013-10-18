#
# Copyright (c) SAS Institute Inc.
#
import os

from conary.lib import options

from .. import errors
from ..lib import command, merge


class MergeCommand(command.BaseCommand):
    help = 'Merge new/changed jobs into new/existing templates'
    commands = ['merge']
    paramHelp = '[options] [TEMPLATE]*'
    requireConfig = True

    def addLocalParameters(self, argDef):
        command.BaseCommand.addLocalParameters(self, argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, templateList = self.requireParameters(args, allowExtra=True)

        projectDir = argSet.get('project', os.getcwd())
        projectDir = os.path.abspath(projectDir)

        # set up template directory
        templateDir = os.path.join(projectDir, cfg.templateDir)
        if not (os.path.exists(templateDir) and os.path.isdir(templateDir)):
            raise errors.CommandError(
                'no template directory found in %s' % projectDir)

        # set up job directory
        jobDir = os.path.join(projectDir, cfg.jobDir)
        if not (os.path.exists(jobDir) and os.path.isdir(jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % projectDir)

        if not templateList:
            templateList = [os.path.join(templateDir, f)
                            for f in os.listdir(templateDir)
                            if f.endswith('.yaml') or f.endswith('.yml')]

        merge.mergeJobs(templateList, jobDir)
