#
# Copyright (c) SAS Institute Inc.
#


import copy
import os

from conary.build import macros as conarymacros
import yaml

from .. import errors
from ..constants import YAML_KWARGS
from ..utils import lxml_utils


def branchJobs(macroList, templateList, jobDir, updateTemplate=False):
    for templateFile in templateList:
        # use template to generate the current set of macros
        with open(templateFile) as fh:
            template = yaml.safe_load(fh)
        curMacros = conarymacros.Macros(
            (k, str(v)) for k, v in template.get('macros'))

        # access the current job file
        curFile = os.path.join(jobDir, template.get('name') % curMacros)
        with open(curFile) as fh:
            jobData = lxml_utils.parse(fh)

        # create a new set of macros from macroList
        newMacros = curMacros.copy()
        newMacros.update(macro for macro in macroList)
        newFile = template.get('name') % newMacros

        # update the jobData
        try:
            newJobData = _updateJobData(
                jobData, template.get('templates'), newMacros)
        except errors.TemplateError as e:
            raise errors.CommandError(
                'Job "%s" %s' % (curFile, e))

        # write new job data to newFile
        with open(os.path.join(jobDir, newFile), 'w') as fh:
            fh.write(lxml_utils.tostring(newJobData))

        if updateTemplate:
            template['macros'] = [
                [macro, value] for macro, value in newMacros.iteritems()]
            with open(templateFile, 'w') as fh:
                fh.write(yaml.safe_dump(template, **YAML_KWARGS))


def _updateJobData(doc, paths, macros):
    newDoc = copy.copy(doc)
    for path, value in paths.iteritems():
        try:
            element = newDoc.xpath(path)[0]
            element.text = value % macros
        except IndexError:
            raise errors.TemplateError('has no element "%s"' % path)
    return newDoc
