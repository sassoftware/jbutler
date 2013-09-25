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
import re
import os

from jbutler import errors
from jbutler.utils import jenkins_utils


def createJobs(cfg, jobList, jobDir):
    """
    Create jenkins jobs using the files listed in jobList

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param jobList: list of jenkins jobs to create
    @type cfg: list
    @param projectPath: path to directory containing jenkins job config files
    """
    jobs = []
    if not os.path.exists(jobDir):
        raise errors.CommandError("no such directory: '%s'" % jobDir)

    # generate a list of job files in jobDir
    jobFiles = [os.path.join(jobDir, f) for f in os.listdir(jobDir)
                if f.endswith('.xml')]

    if not jobFiles:
        print('No jobs found')
        return jobs

    server = jenkins_utils.server_factory(cfg)
    for jobFile in jobFiles:
        jobName, _ = os.path.splitext(jobFile)
        jobName = os.path.basename(jobName)

        # only create jobs that the user supplied
        if jobList and jobName not in jobList:
            continue
        elif jobList:
            jobList.remove(jobName)

        with open(jobFile) as fh:
            if server.has_job(jobName):
                continue
            j = server.create_job(jobname=jobName, config=fh.read())
            jobs.append(j)

    if jobList:
        print("These jobs were not found in the jobs directory: %s" %
              ', '.join([j + '.xml' for j in jobList]))
    return jobs


def retrieveJobs(cfg, jobList, jobDir, jobFilter=None):
    """
    Retrieve jenkins config

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param jobList: list of jenkins jobs to create
    @type cfg: list
    @param projectPath: path to directory containing jenkins job config files
    """
    if not os.path.exists(jobDir):
        raise errors.CommandError("no such directory: '%s'" % jobDir)

    if jobFilter is None:
        jobFilter = '.*'
    jobFilter = re.compile(jobFilter)

    jobs = []
    server = jenkins_utils.server_factory(cfg)

    job_generator = _get_job_generator(server, jobList)
    for jobName, jobObj in job_generator:
        if not jobFilter.match(jobName):
            continue

        jobFile = os.path.join(jobDir, jobName + '.xml')
        with open(jobFile, 'w') as fh:
            fh.write(jobObj.get_config())
        jobs.append(jobObj)
    return jobs


def _get_job_generator(server, jobList=None):
    """
    Create a generator to fetch jobs from a jenkins server
    """
    def _job_generator():
        for jobName in jobList:
            if not server.has_job(jobName):
                print("Server does not have job '%s'" % jobName)
                continue
            yield jobName, server.get_job(jobName)

    if not jobList:
        return server.get_jobs()
    else:
        return _job_generator()
