#
# Copyright (c) SAS Institute Inc.
#


from jenkinsapi.jenkins import Jenkins as _Jenkins

from jbutler.jenkinsapi.view import View
from jbutler.jenkinsapi.views import Views


class Jenkins(_Jenkins):
    @property
    def views(self):
        return Views(self)

    def get_view_by_url(self, str_view_url):
        #for nested view
        str_view_name = str_view_url.split('/view/')[-1].replace('/', '')
        return View(str_view_url, str_view_name, jenkins_obj=self)
