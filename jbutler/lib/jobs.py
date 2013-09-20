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
import os

from jenkinsapi.jenkins import Jenkins

from jbutler import errors


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

    jobFiles = os.listdir(jobDir)
    if not jobFiles:
        return jobs

    jenkins = Jenkins(cfg.server, username=cfg.username, password=cfg.password)
    for jobFile in jobFiles:
        jobName, _ = os.path.splitext(jobFile)

        # only create jobs that the user supplied
        if jobList and jobName not in jobList:
            continue

        with open(jobFile) as fh:
            print("Creating job '%s'" % jobName)
            j = jenkins.create_job(jobname=jobName, config=fh.read())
            jobs.append(j)
    return jobs


def retrieveJobs(cfg, jobList, projectPath):
    """
    Retrieve jenkins config

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param jobList: list of jenkins jobs to create
    @type cfg: list
    @param projectPath: path to directory containing jenkins job config files
    """
    jenkins = Jenkins(cfg.server, username=cfg.username, password=cfg.password,
                      requester=cfg.requester)

    jobs = []
    jobDir = os.path.join(projectPath, 'jobs')
    if not os.path.exists(jobDir):
        raise errors.CommandError("no such directory: '%s'" % jobDir)

    for jobFile in os.listdir(jobDir):
        jobName, _ = os.path.splitext(jobFile)

        # only create jobs that the user supplied
        if jobList and jobName not in jobList:
            continue

        with open(jobFile, 'w') as fh:
            print("Retrieving job '%s'" % jobName)
            job = jenkins.get_job(jobName)
            fh.write(job.get_config())
            jobs.append(job)
    return jobs
