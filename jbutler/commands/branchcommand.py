#
# Copyright (c) SAS Institute Inc.
#


import copy
import os
import warnings

from conary.lib import options

from .. import errors, utils
from ..lib import command


class BranchCommand(command.BaseCommand):
    help = 'Branch existing job configs'
    commands = ['branch']
    paramHelp = '[options] [TEMPLATE]*'
    requireConfig = True

    def _updateJobData(self, doc, paths):
        newDoc = copy.copy(doc)
        for path, value in paths.iteritems():
            try:
                element = newDoc.xpath(path)[0]
                element.text = value % self.toMacros
            except IndexError:
                raise errors.TemplateError(
                    "no element matching xpath '%s'" % (path,))
        return newDoc

    def addParameters(self, argDef):
        command.BaseCommand.addParameters(self, argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')
        argDef['from'] = options.MULT_PARAM, 'Original text'
        argDef['to'] = options.MULT_PARAM, 'Replacement text'

    def runCommand(self, cfg, argSet, args, **kwargs):
        projectDir = argSet.pop('project', os.getcwd())
        fromMacros = argSet.pop('from', None)
        toMacros = argSet.pop('to', None)

        _, templateList = self.requireParameters(args, allowExtra=True)

        if not toMacros:
            raise errors.CommandError(
                "must specify at least one 'to' macro")

        self.fromMacros = utils.parseMacros(fromMacros) if fromMacros else None
        self.toMacros = utils.parseMacros(toMacros)

        self.projectDir = os.path.abspath(projectDir)

        self.jobDir = os.path.join(projectDir, cfg.jobDir)
        # verify jobDir exists
        if not (os.path.exists(self.jobDir) and os.path.isdir(self.jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % projectDir)

        templateDir = os.path.join(projectDir, cfg.templateDir)
        # verify templateDir exists
        if not (os.path.exists(templateDir) and
                os.path.isdir(templateDir)):
            raise errors.CommandError(
                'no templates directory found in %s' % projectDir)
        if not templateList:
            templateList = [os.path.join(templateDir, f)
                            for f in os.listdir(templateDir)
                            if f.endswith('.yaml') or f.endswith('.yml')]

        self.branchJobs(templateList)

    def branchJobs(self, templateList):
        for templateFile in templateList:
            template = utils.readTemplate(templateFile)

            if 'macros' in template:
                warnings.warn(
                    'Support for macros stored in templates is deprecated.',
                    DeprecationWarning,
                    )
                self.fromMacros = utils.parseMacros(
                    '='.join(macro) for macro in template.get('macros'))
            elif not self.fromMacros:
                raise errors.CommandError(
                    "must specify at least one 'from' macro")

            oldFile = os.path.join(
                self.jobDir, template.get('name') % self.fromMacros)
            newFile = os.path.join(
                self.jobDir, template.get('name') % self.toMacros)

            # read job data from oldFile
            jobData = utils.readJob(oldFile)

            # update jobData with toMacros
            try:
                newJobData = self._updateJobData(
                    jobData, template.get('templates') or {})
            except errors.TemplateError as err:
                raise errors.CommandError(
                    "%s parsing job '%s'" % (err, oldFile))

            # write new job data to new file
            utils.writeJob(newFile, newJobData)

            if 'macros' in template:
                # backwards compat for storing macros in templates
                new_template = copy.copy(template)
                for idx, macro in enumerate(new_template.get('macros')):
                    name, value = macro
                    if name in self.toMacros:
                        new_template['macros'][idx][1] = self.toMacros[name]
                utils.writeTemplate(templateFile, new_template)
