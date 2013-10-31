#
# Copyright (c) SAS Institute Inc.
#
"""
Library for working with jenkins jobs
"""
import logging
import re
import os

from lxml import etree

from .. import (
    LXML_KWARGS,
    errors,
    )
from ..utils import jenkins_utils


log = logging.getLogger(__name__)


def createJobs(cfg, jobList, jobDir):
    """
    Create jenkins jobs using the files listed in jobList

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param jobList: list of jenkins jobs to create
    @type cfg: list
    @param projectPath: path to directory containing jenkins job config files
    """
    if not jobList:
        jobList = [os.path.join(jobDir, path) for path in os.listdir(jobDir)]

    server = jenkins_utils.server_factory(cfg)

    jobs = []
    for jobFile in jobList:
        jobName, _ = os.path.splitext(jobFile)
        jobName = os.path.basename(jobName)

        if server.has_job(jobName):
            continue

        with open(jobFile) as fh:
            j = server.create_job(jobname=jobName, config=fh.read())
        jobs.append(j)
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
    for _, jobName in job_generator:
        if not jobFilter.match(jobName):
            continue
        jobObj = server.get_job(jobName)
        jobXmlObj = etree.fromstring(jobObj.get_config())

        jobFile = os.path.join(jobDir, jobName + '.xml')
        with open(jobFile, 'w') as fh:
            fh.write(etree.tostring(jobXmlObj, **LXML_KWARGS))
        jobs.append(jobObj)
    return jobs


def disableJobs(cfg, jobList, jobDir, jobFilter=None, force=False):
    if jobFilter is None:
        jobFilter = '.*'
    jobFilter = re.compile(jobFilter)

    server = jenkins_utils.server_factory(cfg)

    jobs = []
    for _, jobName in _get_job_generator(server, jobList):
        if not jobFilter.match(jobName):
            continue
        jobObj = server.get_job(jobName)
        jobFile = os.path.join(jobDir, jobObj.name + '.xml')
        with open(jobFile) as fh:
            jobXmlObj = etree.parse(fh)

        disabled = jobXmlObj.xpath('/project/disabled')[0]

        jobObj.disable()

        if disabled.text == 'false' and force:
            disabled.text = 'true'
            with open(jobFile, 'w') as fh:
                fh.write(etree.tostring(jobXmlObj, **LXML_KWARGS))
        jobs.append(jobObj)
    return jobs


def enableJobs(cfg, jobList, jobDir, jobFilter=None, force=False):
    if jobFilter is None:
        jobFilter = '.*'
    jobFilter = re.compile(jobFilter)

    server = jenkins_utils.server_factory(cfg)

    jobs = []
    for _, jobName in _get_job_generator(server, jobList):
        if not jobFilter.match(jobName):
            continue
        jobObj = server.get_job(jobName)
        jobFile = os.path.join(jobDir, jobObj.name + '.xml')
        with open(jobFile) as fh:
            jobXmlObj = etree.parse(fh)

        disabled = jobXmlObj.xpath('/project/disabled')[0]
        if disabled.text == 'true' and not force:
            continue
        elif disabled.text == 'true' and force:
            disabled.text = 'false'
            with open(jobFile, 'w') as fh:
                fh.write(etree.tostring(jobXmlObj, **LXML_KWARGS))

        jobObj.enable()
        jobs.append(jobObj)
    return jobs


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
            log.warning("Job does not exist on server: '%s'" % jobName)
    return deleted_jobs


def _get_job_generator(server, jobList=None):
    """
    Create a generator to fetch jobs from a jenkins server
    """
    def _job_generator():
        for jobName in jobList:
            if not server.has_job(jobName):
                print("Server does not have job '%s'" % jobName)
                continue
            yield None, jobName

    if not jobList:
        return server.get_jobs_info()
    else:
        return _job_generator()
