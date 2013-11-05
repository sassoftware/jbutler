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
Library for working with jenkins views
"""
import sys

from ..utils import jenkins_utils


def createViews(cfg, viewList, viewFile):
    """
    Create views

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param viewList: list of view names to create
    @type viewList: list
    @param viewFile: path to file containing view configuration
    @type viewFile: string
    """
    server = jenkins_utils.server_factory(cfg)
    with open(viewFile) as fh:
        views = server.views.createViews(fh.read(), viewList)
    return views


def deleteViews(cfg, viewList, viewFile, force=False):
    """
    Delete views

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param viewList: list of view names to create
    @type viewList: list
    @param viewFile: path to file containing view configuration
    @type viewFile: string
    """
    server = jenkins_utils.server_factory(cfg)

    deleted_views = []
    views = None
    for viewName in viewList:
        if server.has_view(viewName):
            views = server.delete_view(viewName)
            deleted_views.append(viewName)
        else:
            sys.stdout.write(
                "warning: no such view found on server: '%s'\n" % viewName)

    if force and views:
        with open(viewFile, 'w') as fh:
            fh.write(views.serialize())
    return deleted_views


def retrieveViews(cfg, viewList, viewFile):
    """
    Retrieve views from jenkins server

    @param cfg: A config object
    @type cfg: ButlerConfig
    @param viewList: list of view names to create
    @type viewList: list
    @param viewFile: path to file containing view configuration
    @type viewFile: string
    """
    server = jenkins_utils.server_factory(cfg)
    views = server.views.serialize(viewList)
    with open(viewFile, 'w') as fh:
        fh.write(views)
    return views
