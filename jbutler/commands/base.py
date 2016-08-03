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

from ..lib import cfg
from .branch import branch
from .config import config
from .jobs import jobs
from .merge import merge


@click.group()
@click.option('--config', multiple=True, type=(str, str))
@click.option('--config-file', multiple=True,
              type=click.Path(exists=True, dir_okay=False))
@click.option('--skip-default-config/--no-skip-defualt-config', default=False)
@click.option('--quiet/--no-quiet', default=False)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def jbutler(ctx, config, config_file, skip_default_config, quiet, verbose):
    if not skip_default_config:
        config_files = ['/etc/jbutlerrc',
                        os.path.expanduser('~/.jbutlerrc'),
                        './jbutlerrc',
                        ]
    else:
        config_files = []

    if config_file:
        config_files.extend(config_file)

    ctx.obj = cfg.get_config(config_files, **dict(config))

jbutler.add_command(branch)
jbutler.add_command(config)
jbutler.add_command(jobs)
jbutler.add_command(merge)
