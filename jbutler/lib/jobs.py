#
# Copyright (c) SAS Institute Inc.
#
"""
Library for working with jenkins jobs
"""
import os
import re
import sys

from lxml import etree

from .. import (
    LXML_KWARGS,
    errors,
    )
from ..utils import jenkins_utils


def createJobs(cfg, jobList):
    """
    Create jenkins jobs using the files listed in jobList

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param jobList: list of jenkins jobs to create
    @type cfg: list
    @param projectPath: path to directory containing jenkins job config files
    """
    server = jenkins_utils.server_factory(cfg)

    created_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(jobFile)
        jobName = os.path.basename(jobName)

        if server.has_job(jobName):
            continue

        with open(jobFile) as fh:
            j = server.create_job(jobname=jobName, config=fh.read())
        created_jobs.append(j)
    return created_jobs


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
    server = jenkins_utils.server_factory(cfg)

    if jobFilter is None:
        jobFilter = '.*'
    jobFilter = re.compile(jobFilter)

    retrieved_jobs = []
    for _, jobName in _get_job_generator(server, jobList):
        if jobFilter.match(jobName):
            jobObj = server.get_job(jobName)
            jobXmlObj = etree.fromstring(jobObj.get_config())

            jobFile = os.path.join(jobDir, jobName + '.xml')
            with open(jobFile, 'w') as fh:
                fh.write(etree.tostring(jobXmlObj, **LXML_KWARGS))
            retrieved_jobs.append(jobObj)
    return retrieved_jobs


def disableJobs(cfg, jobList, force=False):
    server = jenkins_utils.server_factory(cfg)

    disabled_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile))

        if server.has_job(jobName):
            jobObj = server.get_job(jobName)
            with open(jobFile) as fh:
                jobXmlObj = etree.parse(fh)

            disabled = jobXmlObj.xpath('/project/disabled')
            if not disabled:
                raise errors.CommandError(
                    "Job config does not have a 'disabled' property")
            disabled = disabled[0]

            jobObj.disable()

            if disabled.text == 'false' and force:
                disabled.text = 'true'
                with open(jobFile, 'w') as fh:
                    fh.write(etree.tostring(jobXmlObj, **LXML_KWARGS))
            disabled_jobs.append(jobObj)
        else:
            sys.stdout.write(
                "warning: no such job on server: '%s'\n" % jobName)

    return disabled_jobs


def enableJobs(cfg, jobList, force=False):
    server = jenkins_utils.server_factory(cfg)

    enabled_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile))

        if server.has_job(jobName):
            jobObj = server.get_job(jobName)
            with open(jobFile) as fh:
                jobXmlObj = etree.parse(fh)

            disabled = jobXmlObj.xpath('/project/disabled')
            if not disabled:
                raise errors.CommandError(
                    "Job config does not have a 'disabled' property")
            disabled = disabled[0]

            if disabled.text == 'true' and force:
                disabled.text = 'false'
                with open(jobFile, 'w') as fh:
                    fh.write(etree.tostring(jobXmlObj, **LXML_KWARGS))

            if disabled.text == 'false' and not jobObj.is_enabled():
                jobObj.enable()
                enabled_jobs.append(jobObj)
        else:
            sys.stdout.write(
                "warning: no such job on server: '%s'\n" % jobName)
    return enabled_jobs


def deleteJobs(cfg, jobList, force=False):
    '''
    Delete the jobs in jobList. If force is True, also delete the local
    config file

    @param cfg: configuration
    @type cfg: JButlerCfg
    @param jobList: list of job config files
    @type jobList: list
    @param force: if true, delete the local config files
    @type: bool
    '''
    server = jenkins_utils.server_factory(cfg)

    deleted_jobs = []
    for jobFile in jobList:
        if not os.path.exists(jobFile):
            raise errors.CommandError(
                "[Errno 2]: No such file or directory: '%s'" % jobFile)

        jobName, _ = os.path.splitext(os.path.basename(jobFile))
        if server.has_job(jobName):
            server.delete_job(jobName)
            deleted_jobs.append(jobFile)
            if force:
                os.remove(jobFile)
        else:
            sys.stdout.write(
                "warning: job does not exist on server: '%s'\n" % jobName)
    return deleted_jobs


def updateJobs(cfg, jobList):
    '''
    Update an existing jenkins job to match the local config

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param jobList: list of jenkins jobs to update
    @type jobList: list
    '''
    server = jenkins_utils.server_factory(cfg)

    updated_jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(os.path.basename(jobFile))

        if server.has_job(jobName):
            with open(jobFile) as fh:
                job = server.update_job(jobname=jobName, config=fh.read())
            updated_jobs.append(job)
        else:
            sys.stdout.write(
                "warning: job does not exist on server: '%s'\n" % jobName)
    return updated_jobs


def _get_job_generator(server, jobList=None):
    """
    Create a generator to fetch jobs from a jenkins server
    """
    def _job_generator():
        for jobName in jobList:
            if not server.has_job(jobName):
                sys.stdout.write(
                    "warning: server does not have job '%s'\n" % jobName)
                continue
            yield None, jobName

    if not jobList:
        return server.get_jobs_info()
    else:
        return _job_generator()
