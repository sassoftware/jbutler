#
# Copyright (c) SAS Institute Inc.
#
from . import (
    branchcommand,
    configcommand,
    helpcommand,
    jobscommand,
    mergecommand,
    viewscommand,
    )


commandList = [
    branchcommand.BranchCommand,
    configcommand.ConfigCommand,
    helpcommand.HelpCommand,
    jobscommand.JobCommand,
    mergecommand.MergeCommand,
    viewscommand.ViewCommand,
    ]
