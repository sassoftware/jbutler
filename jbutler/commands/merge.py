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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import copy
import difflib
import os
import re

import click
import six

from .. import errors, utils


YES = ('y', 'Y', '')
NO = ('n', 'N')
QUIT = ('q', 'Q')
MACRO_RE = re.compile(r'%\(\w+\)s')


def _mergeTemplate(template, job, macros):
    newTemplate = copy.copy(template)
    template_pairs = _mergeTemplateHelper(job.getroot(), template, job, macros)
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
    for macro, value in six.iteritems(macros):
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
        click.echo('File: ' + jobTemplate.get('name') % macros)
        click.echo(xpath + ':\n')
        diff = difflib.ndiff([old_template + '\n'], [new_template + '\n'])
        click.echo(''.join(diff))

        response = None
        while response not in YES + NO + QUIT:
            response = click.prompt(prompt, default='y')
        click.echo('\n')

        if response in YES:
            if not prompt.startswith('Remove'):
                template_pairs.append((xpath, new_template))
        elif response in NO:
            if old_template:
                template_pairs.append((xpath, old_template))
        elif response in QUIT:
            raise click.Abort()
    elif old_template:
        template_pairs.append((xpath, old_template))

    for child in node.iterchildren():
        template_pairs.extend(
            _mergeTemplateHelper(child, jobTemplate, jobConfig, macros))

    return template_pairs


def _mergeJobs(templateList, jobDir, fromMacros):
    for templateFile in templateList:
        template = utils.readTemplate(templateFile)

        jobFile = os.path.join(
            jobDir, template.get('name') % fromMacros)

        jobData = utils.readJob(jobFile)

        try:
            mergedTemplate = _mergeTemplate(template, jobData, fromMacros)
        except errors.TemplateError as err:
            raise errors.CommandError(
                u"%s parsing job '%s'" % (err, jobFile))

        utils.writeTemplate(templateFile, mergedTemplate)


@click.command()
@click.option('-f', '--from', 'from_macros', nargs=2, required=True,
              multiple=True)
@click.argument('templates', nargs=-1, type=click.Path(
    dir_okay=False, readable=True, resolve_path=True))
@click.pass_obj
def merge(cfg, from_macros, templates):
    from_macros = dict(m for m in from_macros)

    template_dir = cfg.templatedir
    if not templates:
        templates = [os.path.join(template_dir, f)
                     for f in os.listdir(template_dir)
                     if f.endswith('.yaml') or f.endswith('.yml')]

    _mergeJobs(templates, cfg.jobdir, from_macros)
