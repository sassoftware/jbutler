#
# Copyright (c) SAS Institute Inc.
#


import os

from conary.lib import options

from .. import errors
from ..lib import branch, command


class BranchCommand(command.BaseCommand):
    help = 'Branch existing job configs'
    commands = ['branch']
    paramHelp = '[options] [MACRO]+'
    requireConfig = True

    def addParameters(self, argDef):
        command.BaseCommand.addParameters(self, argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')
        argDef['template'] = (options.MULT_PARAM, 'Path to template file to'
                              ' branch')

    def runCommand(self, cfg, argSet, args, **kwargs):
        _, argList = self.requireParameters(args, allowExtra=True)

        if not argList:
            raise errors.CommandError(
                'must specify at least one macro')

        macroList = []
        for arg in argList:
            macro, sep, value = arg.partition('=')
            if not (macro and sep and value):
                raise errors.CommandError(
                    'incorrect macro "%s". expected "<macro>=<value>"' % arg)
            macroList.append((macro, value))

        projectDir = argSet.get('project', os.getcwd())
        templateList = argSet.get('template')

        projectDir = os.path.abspath(projectDir)

        jobDir = os.path.join(projectDir, cfg.jobDir)
        # verify jobDir exists
        if not (os.path.exists(jobDir) and os.path.isdir(jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % projectDir)

        if not templateList:
            templateDir = os.path.join(projectDir, cfg.templateDir)
            # verify templateDir exists
            if not (os.path.exists(templateDir) and
                    os.path.isdir(templateDir)):
                raise errors.CommandError(
                    'no templates directory found in %s' % projectDir)
            templateList = [os.path.join(templateDir, f)
                            for f in os.listdir(templateDir)
                            if f.endswith('.yaml') or f.endswith('.yml')]

        branch.branchJobs(macroList, templateList, jobDir, True)
