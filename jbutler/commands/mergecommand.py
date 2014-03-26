#
# Copyright (c) SAS Institute Inc.
#
import copy
import difflib
import os
import re
import sys

from conary.lib import options

from .. import errors, utils
from ..lib import command


YES = ('y', 'Y', '')
NO = ('n', 'N')
QUIT = ('q', 'Q')
MACRO_RE = re.compile(r'%\(\w+\)s')


class MergeCommand(command.BaseCommand):
    help = 'Merge new/changed jobs into new/existing templates'
    commands = ['merge']
    paramHelp = '[options] [TEMPLATE]*'
    requireConfig = True

    def _mergeTemplate(self, template, job):
        newTemplate = copy.copy(template)
        template_pairs = self._mergeTemplateHelper(
            job.getroot(),
            template,
            job,
            )
        newTemplate['templates'] = dict((k, v) for k, v in template_pairs)
        return newTemplate

    def _mergeTemplateHelper(self, node, jobTemplate, jobConfig):
        template_pairs = []
        templates = jobTemplate.get('templates')
        if templates is None:
            templates = {}

        # process node
        xpath = jobConfig.getpath(node)
        old_template = templates.get(xpath, '')
        new_template = node.text or ''
        for macro, value in self.fromMacros.itermacros():
            new_template = new_template.replace(value, '%%(%s)s' % macro)

        isTemplated = MACRO_RE.search(new_template)
        prompt = None
        if old_template and isTemplated:
            # update existing node
            if old_template != new_template:
                prompt = 'Update the template for this node [Y/n/q]? '
        elif old_template and not isTemplated:
            # remove old node
            prompt = 'Remove this node from template [Y/n/q]? '
        elif not old_template and isTemplated:
            # add new templated node
            prompt = 'Add this node to template [Y/n/q]? '

        if prompt:
            sys.stdout.write(
                'File: ' + jobTemplate.get('name') % self.fromMacros + '\n')
            sys.stdout.write(xpath + ':\n')
            diff = difflib.ndiff([old_template + '\n'], [new_template + '\n'])
            sys.stdout.write(''.join(diff) + '\n')

            response = None
            while not response in YES + NO + QUIT:
                response = raw_input(prompt)
            sys.stdout.write('\n\n')

            if response in YES:
                if not prompt.startswith('Remove'):
                    template_pairs.append((xpath, new_template))
            elif response in NO:
                if old_template:
                    template_pairs.append((xpath, old_template))
            elif response in QUIT:
                raise KeyboardInterrupt
        elif old_template:
            template_pairs.append((xpath, old_template))

        for child in node.iterchildren():
            template_pairs.extend(
                self._mergeTemplateHelper(child, jobTemplate, jobConfig))

        return template_pairs

    def addLocalParameters(self, argDef):
        command.BaseCommand.addLocalParameters(self, argDef)
        argDef['project'] = (options.OPT_PARAM, 'Path to project, defaults to'
                             ' current working directory')
        argDef['from'] = options.MULT_PARAM, 'Macro to do replacement on'

    def mergeJobs(self, templateList):
        for templateFile in templateList:
            template = utils.readTemplate(templateFile)

            jobFile = os.path.join(
                self.jobDir, template.get('name') % self.fromMacros)

            jobData = utils.readJob(jobFile)

            try:
                mergedTemplate = self._mergeTemplate(template, jobData)
            except errors.TemplateError as err:
                raise errors.CommandError(
                    "%s parsing job '%s'" % (err, jobFile))

            utils.writeTemplate(templateFile, mergedTemplate)

    def runCommand(self, cfg, argSet, args, **kwargs):
        projectDir = argSet.pop('project', os.getcwd())
        fromMacros = argSet.pop('from', [])

        _, templateList = self.requireParameters(args, allowExtra=True)

        self.fromMacros = utils.parseMacros(fromMacros)

        self.projectDir = os.path.abspath(projectDir)

        # set up job directory
        self.jobDir = os.path.join(projectDir, cfg.jobDir)
        if not (os.path.exists(self.jobDir) and os.path.isdir(self.jobDir)):
            raise errors.CommandError(
                'no jobs directory found in %s' % projectDir)

        # set up template directory
        self.templateDir = os.path.join(self.projectDir, cfg.templateDir)
        if not (os.path.exists(self.templateDir)
                and os.path.isdir(self.templateDir)):
            raise errors.CommandError(
                'no template directory found in %s' % projectDir)

        if not templateList:
            templateList = [os.path.join(self.templateDir, f)
                            for f in os.listdir(self.templateDir)
                            if f.endswith('.yaml') or f.endswith('.yml')]

        self.mergeJobs(templateList)
