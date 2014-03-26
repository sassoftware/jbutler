#
# Copyright (c) SAS Institute Inc.
#
import copy
import difflib
import os
import sys

from conary.build import macros as conarymacros
from lxml import objectify
import yaml

from .. import errors
from ..constants import YES, NO, QUIT, MACRO_RE


def mergeJobs(templateList, jobDir):
    for templateFile in templateList:
        # load template yaml
        with open(templateFile) as fh:
            template = yaml.safe_load(fh)
        macros = conarymacros.Macros(
            (k, str(v)) for k, v in template.get('macros'))

        # load the matching job file
        jobFile = template.get('name') % macros
        with open(os.path.join(jobDir, jobFile)) as fh:
            jobData = objectify.parse(fh)

        try:
            mergedTemplate = _mergeTemplate(template, jobData, macros)
        except errors.TemplateError as e:
            raise errors.CommandError('Job "%s" %s' % (jobFile, e))

        # write new template
        with open(templateFile, 'w') as fh:
            yaml.safe_dump(mergedTemplate, fh, default_flow_style=False)


def _mergeTemplate(template, job, macros):
    newTemplate = copy.copy(template)
    template_pairs = _mergeTemplateHelper(
        job.getroot(),
        template,
        job,
        macros,
        )
    newTemplate['templates'] = dict((k, v) for k, v in template_pairs)
    return newTemplate


def _mergeTemplateHelper(node, jobTemplate, jobConfig, macros):
    template_pairs = []
    templates = jobTemplate.get('templates')
    if templates is None:
        templates = {}

    # process node
    xpath = jobConfig.getpath(node)
    old_template = templates.get(xpath, '')
    new_template = node.text or ''
    for macro, value in macros.itermacros():
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
        sys.stdout.write('File: ' + jobTemplate.get('name') % macros + '\n')
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
            _mergeTemplateHelper(child, jobTemplate, jobConfig, macros))

    return template_pairs
