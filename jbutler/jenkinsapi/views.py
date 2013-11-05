#
# Copyright (c) SAS Institute Inc.
#


import logging
import urllib

from jenkinsapi.views import Views as _Views
import yaml

from .. import VIEW_SEP, YAML_KWARGS
from .view import View


(LIST_VIEW, NESTED_VIEW) = (_Views.LIST_VIEW, _Views.NESTED_VIEW)
FIELDS = ('name', 'description', 'filterQueue', 'filterExecutors',)
LIST_FIELDS = FIELDS + ('statusFilter', 'recurse',)
NESTED_FIELDS = FIELDS + ('defaultView',)


log = logging.getLogger(__name__)


class Views(_Views):

    def __contains__(self, view_path):
        return (self.get_view_by_path(view_path) is not None)

    def __getitem__(self, view_name):
        for row in self.jenkins._data.get('views', []):
            if row['name'] == view_name:
                return View(
                    row['url'],
                    row['name'],
                    self.jenkins)
        else:
            return None

    def _from_yaml(self, data, viewList=None):
        return [self.createView(viewObj) for viewObj in yaml.safe_load(data)
                if not viewList or viewObj['name'] in viewList]

    def _to_yaml(self, viewObjs):
        return yaml.safe_dump(viewObjs, default_flow_style=False)

    def createView(self, viewObj):
        """
        Create a view and all sub-views from a viewObj
        """
        viewName = viewObj['name']
        viewType = NESTED_VIEW if 'views' in viewObj else LIST_VIEW
        view = self.create(viewName, viewType)

        if viewType == LIST_VIEW:
            view = self._configureListView(view, viewObj)
            return [view]

        if viewType == NESTED_VIEW and viewObj['views']:
            return [view] + [view.views.createView(v)
                             for v in viewObj['views']]

    def _configureListView(self, view, viewConfig):
        log.info('Configuring "%s" view' % (view.name,))

        url = '%s/configSubmit' % view.baseurl
        json_data = dict((k, v) for k, v in viewConfig.items()
                         if k in LIST_FIELDS)

        json_data[''] = json_data.get('description', '')
        if 'includeRegex' in viewConfig:
            json_data['useincluderegex'] = {
                'includeRegex': viewConfig['includeRegex'],
                }
        json_data['columns'] = [
            {"stapler-class": "hudson.views.StatusColumn",
                "kind": "hudson.views.StatusColumn"},
            {"stapler-class": "hudson.views.WeatherColumn",
                "kind": "hudson.views.WeatherColumn"},
            {"stapler-class": "hudson.views.JobColumn",
                "kind": "hudson.views.JobColumn"},
            {"stapler-class": "hudson.views.LastSuccessColumn",
                "kind": "hudson.views.LastSuccessColumn"},
            {"stapler-class": "hudson.views.LastFailureColumn",
                "kind": "hudson.views.LastFailureColumn"},
            {"stapler-class": "hudson.views.LastDurationColumn",
                "kind": "hudson.views.LastDurationColumn"},
            {"stapler-class": "hudson.views.BuildButtonColumn",
                "kind": "hudson.views.BuildButtonColumn"},
            ]

        for jobName in viewConfig.get('jobs', []):
            json_data[jobName] = True

        json_data['core:apply'] = ''

        data = {}
        for key, value in json_data.items():
            if key == 'useincluderegex':
                data['includeRegex'] = value['includeRegex']
                value = 'on'
            elif isinstance(value, bool):
                if not value:
                    continue
                value = 'on'
            data[key] = value

        data['json'] = json_data
        data['Submit'] = 'OK'

        self.jenkins.requester.post_and_confirm_status(
            url, data=urllib.urlencode(data))
        self.jenkins.poll()
        return self[view.name]

    def createViews(self, data, viewList=None, serialization='yaml'):
        deserializer = getattr(self, '_from_%s' % serialization)
        return deserializer(data, viewList)

    def delete(self, view_path):
        view = self.get_view_by_path(view_path)
        self.delete_view_by_url(view.baseurl)

    def delete_view_by_url(self, str_url):
        url = "%s/doDelete" % str_url
        self.jenkins.requester.post_and_confirm_status(url, data='')
        self.jenkins.poll()
        return self

    def get_view_by_path(self, view_path):
        root_view, _, subpath = view_path.partition(VIEW_SEP)
        try:
            if subpath:
                return self[root_view].views.get_view_by_path(subpath)
            else:
                return self[root_view]
        except (AttributeError, KeyError):
            return None

    def serialize(self, viewList=None, serialization='yaml'):
        viewObjs = []
        for viewName, view in self.iteritems():
            if 'nodeDescription' in view._data:
                continue

            if viewList and viewName not in viewList:
                continue

            viewObj = view.toDict()
            viewObjs.append(viewObj)

        serializer = getattr(self, '_to_%s' % serialization)
        return serializer(viewObjs)

    def iteritems(self):
        """
        Get the names & objects for all views
        """
        self.jenkins.poll()
        for row in self.jenkins._data.get('views', []):
            name = row['name']
            url = row['url']

            yield name, View(url, name, self.jenkins)
