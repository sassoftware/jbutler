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
job command and sub-commands
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import click

from ..lib import jobs as libjobs
from ..utils import jenkins_utils
from ..utils import lxml_utils


@click.group(help='Manage jenkins jobs')
def jobs():
    pass


@jobs.command()
@click.argument('jobs', nargs=-1, type=click.File(), required=True)
@click.option('--watch/--no-watch', default=True,
              help='Whether to monitor the job console output')
@click.pass_obj
def build(cfg, jobs, watch):
    """Start a build of a jenkins job"""
    libjobs.buildJobs(cfg, jobs, watch)


@jobs.command()
@click.argument('jobs', nargs=-1, type=click.File(), required=True)
@click.pass_obj
def create(cfg, jobs):
    """Create a jenkins job"""
    server = jenkins_utils.server_factory(cfg)
    libjobs.createJobs(server, jobs)


@jobs.command()
@click.argument('jobs', nargs=-1)
@click.option('--filter', metavar='PATTERN',
              help='Only retrieve jobs that match the regex PATTERN')
@click.pass_obj
def retrieve(cfg, jobs, filter):
    """Retrieve a jenkins job"""
    server = jenkins_utils.server_factory(cfg)
    retrieved = libjobs.retrieveJobs(server, jobs, filter)
    for job in retrieved:
        job_file = os.path.join(cfg.jobdir, job.name + '.xml')
        with open(job_file, 'w') as fh:
            fh.write(job.get_config())


@jobs.command()
@click.argument('jobs', nargs=-1, required=True,
                type=click.Path(exists=True, writable=True, dir_okay=False))
@click.option('--force/--no-force', default=False,
              help='Update local config file')
@click.pass_obj
def disable(cfg, jobs, force):
    """Disable jenkins job"""
    server = jenkins_utils.server_factory(cfg)
    disabled = libjobs.disableJobs(server, jobs)
    if force:
        for job_file in disabled:
            with open(job_file) as fh:
                job_xml = lxml_utils.parse(fh)
            d = job_xml.xpath('/project/disabled')
            if not d:
                click.echo(u"Warning: job config does not have a 'disabled' "
                           u"property: '%s'" % job_file, err=True)
            else:
                d = d[0]
                if d.text == 'false':
                    d.text = 'true'
                    with open(job_file, 'wb') as fh:
                        fh.write(lxml_utils.tostring(job_xml))


@jobs.command()
@click.argument('jobs', nargs=-1, required=True,
                type=click.Path(exists=True, writable=True, dir_okay=False))
@click.option('--force/--no-force', default=False,
              help='Update local config file')
@click.pass_obj
def enable(cfg, jobs, force):
    """Enable jenkins job"""
    server = jenkins_utils.server_factory(cfg)
    enabled = libjobs.enableJobs(server, jobs)
    if force:
        for job_file in enabled:
            with open(job_file) as fh:
                job_xml = lxml_utils.parse(fh)
            d = job_xml.xpath('/project/disabled')
            if not d:
                click.echo(u"Warning: job config does not have a 'disabled' "
                           u"property: '%s'" % job_file, err=True)
            else:
                d = d[0]
                if d.text == 'true':
                    d.text = 'false'
                    with open(job_file, 'wb') as fh:
                        fh.write(lxml_utils.tostring(job_xml))


@jobs.command()
@click.argument('jobs', nargs=-1, required=True,
                type=click.Path(exists=True, writable=True, dir_okay=False))
@click.option('--force/--no-force', default=False,
              help='Delete local config file')
@click.pass_obj
def delete(cfg, jobs, force):
    """Delete jenkins job"""
    server = jenkins_utils.server_factory(cfg)
    deleted = libjobs.deleteJobs(server, jobs)
    if force:
        for job_name in deleted:
            job_file = os.path.join(cfg.jobdir, job_name + '.xml')
            os.remove(job_file)


@jobs.command()
@click.argument('jobs', nargs=-1, type=click.File(), required=True)
@click.pass_obj
def update(cfg, jobs):
    """Update a jenkins job"""
    server = jenkins_utils.server_factory(cfg)
    libjobs.updateJobs(server, jobs)
