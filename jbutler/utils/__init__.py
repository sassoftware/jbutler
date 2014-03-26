#
# Copyright (c) SAS Institute Inc.
#

from conary.build.macros import Macros
import yaml

from . import lxml_utils
from .. import errors
from ..constants import YAML_KWARGS


def parseMacros(macroList):
    macros = Macros()
    for string in macroList:
        macro, sep, value = string.partition('=')
        if not (macro and sep and value):
            raise errors.CommandError(
                'incorrect macro "%s". expected "<macro>=<value>"' %
                (string,))
        setattr(macros, macro, value)
    return macros


def readJob(filename):
    with open(filename) as fh:
        return lxml_utils.parse(fh)


def readTemplate(filename):
    with open(filename) as fh:
        return yaml.safe_load(fh)


def writeJob(filename, data):
    with open(filename, 'w') as fh:
        fh.write(lxml_utils.tostring(data))


def writeTemplate(filename, data):
    with open(filename, 'w') as fh:
        yaml.safe_dump(data, fh, **YAML_KWARGS)
