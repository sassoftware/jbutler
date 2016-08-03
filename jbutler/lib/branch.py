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
import os
import warnings

import click

from .. import errors
from .. import utils


def branch_jobs(templates, from_macros, to_macros, job_dir):
    for template in templates:
        template = utils.readTemplate(template)

        if 'macros' in template:
            warnings.warn(
                'Support for macros stored in templates is deprecated.',
                DeprecationWarning,
            )
            from_macros = dict((m, v) for m, v in template.get('macros'))
        elif not from_macros:
            click.echo(u"Cannot process template '%s', must specify at least "
                       u"one 'from' macro", err=True)
            continue

        old_file = os.path.join(job_dir, template.get('name') % from_macros)
        new_file = os.path.join(job_dir, template.get('name') % to_macros)

        # read job data from oldFile
        job_data = utils.readJob(old_file)

        # update jobData with toMacros
        try:
            new_job_data = _update_job_data(
                job_data, template.get('templates') or {}, to_macros)
        except errors.TemplateError as err:
            raise errors.CommandError(
                u"%s parsing job '%s'" % (err, old_file))

        # write new job data to new file
        utils.writeJob(new_file, new_job_data)

        if 'macros' in template:
            # backwards compat for storing macros in templates
            new_template = copy.copy(template)
            for idx, macro in enumerate(new_template.get('macros')):
                name, value = macro
                if name in to_macros:
                    new_template['macros'][idx][1] = to_macros[name]
            utils.writeTemplate(template, new_template)


def _update_job_data(doc, paths, macros):
    newDoc = copy.copy(doc)
    for path, value in paths.items():
        try:
            element = newDoc.xpath(path)[0]
            element.text = value % macros
        except IndexError:
            raise errors.TemplateError(
                u"no element matching xpath '%s'" % (path,))
    return newDoc
