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
Library for working with jenkins jobs
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging
import os
import re
import time
import threading

from jenkinsapi.custom_exceptions import NotBuiltYet
from jenkinsapi.queue import QueueItem
from requests import HTTPError
import click

log = logging.getLogger(__name__)


def createJobs(server, jobList):
    """Create jenkins jobs using the files listed in jobList

    :param server: A jenkins server
    :type server: :class:`jenkinsapi.jenkins.Jenkins`
    :param jobList: list of file-like objects
    :type jobList: list
    """
    created_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile.name))

        if not server.has_job(jobName):
            j = server.create_job(jobName, jobFile.read())
            created_jobs.append(j)
        else:
            click.echo(u"warning: job already exists on server: '%s'" %
                       jobName, err=True)
    return created_jobs


def retrieveJobs(server, jobList, jobFilter=None):
    """Retrieve jenkins config

    :param server: configuration object
    :type cfg: :class:`jenkinsapi.Jenkins`
    :param list jobList: list of job names to retrieve
    :param str jobFilter: regex to filter jobs with or None
    :returns: list of :class:`jenkinsapi.Job`s
    """
    if jobFilter is None:
        jobFilter = '.*'
    jobFilter = re.compile(jobFilter)

    retrieved_jobs = []
    for jobUrl, jobName in _get_job_generator(server, jobList):
        if jobFilter.match(jobName):
            retrieved_jobs.append(server.get_job(jobName))
    return retrieved_jobs


def disableJobs(server, jobList):
    """Disable josb in `jobList`

    :param server: Jenkins server
    :type server: :class:`jenkinsapi.Jenkins`
    :param list jobList: job configuration files
    :returns: list of job files that were disabled
    """
    disabled_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile))
        if server.has_job(jobName):
            jobObj = server.get_job(jobName)
            if jobObj.is_enabled():
                jobObj.disable()
                disabled_jobs.append(jobFile)
        else:
            click.echo(u"warning: no such job: '%s'" % jobName,
                       err=True)
    return disabled_jobs


def enableJobs(server, jobList):
    """Enable josb in `jobList`

    :param server: Jenkins server
    :type server: :class:`jenkinsapi.Jenkins`
    :param list jobList: job configuration files
    :returns: list of job files that were enabled
    """
    enabled_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile))
        if server.has_job(jobName):
            jobObj = server.get_job(jobName)
            if not jobObj.is_enabled():
                jobObj.enable()
                enabled_jobs.append(jobFile)
        else:
            click.echo(u"warning: no such job: '%s'" % jobName,
                       err=True)
    return enabled_jobs


def deleteJobs(server, jobList):
    """Delete the jobs in `jobList`.

    :param server: jenkins server
    :type server: :class:`jenkinsapi.jenkins.Jenkins`
    :param list jobList: list of job config file names
    """
    deleted_jobs = []
    for job_file in jobList:
        job_name, _ = os.path.splitext(os.path.basename(job_file))
        if server.has_job(job_name):
            server.delete_job(job_name)
            deleted_jobs.append(job_name)
        else:
            click.echo(u"warning: no such job: '%s'" % job_name,
                       err=True)
    return deleted_jobs


def updateJobs(server, jobList):
    """Update an existing jenkins job to match the local config

    :param server: A jenkins server
    :type server: :class:`jenkinsapi.jenkins.Jenkins`
    :param list jobList: list of job config files
    """
    updated_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile.name))

        if server.has_job(jobName):
            job = server.get_job(jobName)
            job.update_config(jobFile.read())
            updated_jobs.append(job)
        else:
            click.echo(u"warning: no such job: '%s'" % jobName,
                       err=True)
    return updated_jobs


def buildJobs(server, jobList, watch=True, params=None):
    """Trigger a job to build

    :param jbutler.ButlerConfig cfg: configuration
    :param list jobList: list of jenkins job names
    """
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile))

        if server.has_job(jobName):
            qi = server[jobName].invoke(build_params=params or {})
            if watch:
                t = threading.Thread(target=_watch_job, args=(qi,))
                t.daemon = True
                t.start()

    while threading.active_count() > 0:
        time.sleep(0.1)


def _get_job_generator(server, jobList=None):
    """Create a generator to fetch jobs from a jenkins server"""
    jobs = server.get_jobs_info()
    if not jobList:
        return jobs
    jobsDict = dict((name, url) for url, name in jobs)
    ret = []
    for jobName in jobList:
        jobUrl = jobsDict.get(jobName)
        if jobUrl is None:
            click.echo(u"warning: no such job: '%s'" % jobName,
                       err=True)
        else:
            ret.append((jobUrl, jobName))
    return ret


def _watch_job(job, delay=5):
    waited = 0
    idx = 0
    while True:
        job.poll()
        if isinstance(job, QueueItem):
            try:
                job = job.get_build()
            except (NotBuiltYet, HTTPError):
                click.echo('[%s] Waited %is for start' % (job.name, waited))
                waited += delay
                time.sleep(delay)
        else:
            console = job.get_console().split('\n')
            output = console[idx:]
            if output:
                for line in output:
                    if line:
                        click.echo('[%s] %s\n' % (job.name, line))
            idx = len(console) - 1
            if not job.is_running():
                return
