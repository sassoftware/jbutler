#
# Copyright (c) SAS Institute Inc.
#


import logging
import urllib

from jenkinsapi.views import Views as _Views
import yaml

from ..constants import VIEW_SEP, YAML_KWARGS
from .view import View


(LIST_VIEW, NESTED_VIEW) = (_Views.LIST_VIEW, _Views.NESTED_VIEW)
FIELDS = ('name', 'description', 'filterQueue', 'filterExecutors',)
LIST_FIELDS = FIELDS + ('statusFilter', 'recurse',)
NESTED_FIELDS = FIELDS + ('defaultView',)


log = logging.getLogger(__name__)


class Views(_Views):
    '''
    Wrapper around jenkinsapi Views object
    '''
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

    def _from_yaml(self, data):
        return yaml.safe_load(data)

    def _to_yaml(self, view_objs):
        return yaml.safe_dump(view_objs, **YAML_KWARGS)

    def _createView(self, view_obj, parent_view, view_list=None, force=False):
        """
        Create a view and all sub-views from a viewObj
        """
        if parent_view is None:
            raise Exception(
                "trying to create child view of non-existant parent: '%s'" %
                view_obj['path'])

        if not view_list or view_obj['path'] in view_list:
            view = self._create_view_helper(view_obj, parent_view, force)
            created_views = [view]
        else:
            view = self.get_view_by_path(view_obj['path'])
            created_views = []

        for subview in view_obj.get('views', []):
            created_views.extend(
                self._createView(subview, view.views, view_list))
        return created_views

    def _create_view_helper(self, view_obj, parent_view, force=False):
        view_name = view_obj['name']
        view_type = NESTED_VIEW if 'views' in view_obj else LIST_VIEW

        if view_name not in parent_view or force:
            view = parent_view.create(view_name, view_type)

            if view_type == LIST_VIEW:
                view = self._configureListView(view, view_obj)
        else:
            view = parent_view[view_name]
        return view

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

    def deserialize(self, data, view_list=None, serialization='yaml',
                    update=False):
        deserializer = getattr(self, '_from_%s' % serialization)

        created_views = []
        for view_obj in deserializer(data):
            created_views.extend(
                self._createView(view_obj, self, view_list, update))
        return created_views

    def delete(self, view_path):
        view = self.get_view_by_path(view_path)
        self.delete_view_by_url(view.baseurl)

    def delete_view_by_url(self, str_url):
        url = "%s/doDelete" % str_url
        self.jenkins.requester.post_and_confirm_status(url, data='')
        self.jenkins.poll()
        return self

    def get_view_by_path(self, view_path):
        root_path, _, view_name = view_path.rpartition(VIEW_SEP)
        try:
            if root_path:
                return self.get_view_by_path(root_path).views[view_name]
            else:
                return self[view_name]
        except (AttributeError, KeyError):
            return None

    def serialize(self, viewList=None, serialization='yaml', root_path=None):
        viewObjs = []
        for viewName, view in self.iteritems():
            if 'nodeDescription' in view._data:
                continue

            if viewList and viewName not in viewList:
                continue

            viewObj = view.toDict(root_path)
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
