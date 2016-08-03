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
import os

import click

from ..lib import branch as libbranch


@click.command()
@click.option('-f', '--from', 'from_macros', nargs=2, multiple=True)
@click.option('-t', '--to', 'to_macros', nargs=2, required=True,
              multiple=True)
@click.argument('templates', nargs=-1,
                type=click.Path(dir_okay=False, readable=True,
                                resolve_path=True))
@click.pass_obj
def branch(cfg, from_macros, to_macros, templates):
    from_macros = dict(m for m in from_macros) if from_macros else None
    to_macros = dict(m for m in to_macros)

    if not templates:
        templates = [os.path.join(cfg.templatedir, f)
                     for f in os.listdir(cfg.templatedir)
                     if f.endswith('.yaml') or f.endswith('.yml')]

    libbranch.branch_jobs(templates, from_macros, to_macros, cfg.jobdir)
