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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from jenkinsapi.jenkins import Jenkins as _Jenkins
from jenkinsapi.custom_exceptions import UnknownJob, JenkinsAPIException

from .view import View
from .views import Views


class Jenkins(_Jenkins):
    def _clone(self):
        return Jenkins(
            self.baseurl,
            username=self.username,
            password=self.password,
            requester=self.requester,
        )

    def delete_view(self, view_name):
        return self.views.delete(view_name)

    def get_jenkins_obj_from_url(self, url):
        return Jenkins(url, self.username, self.password, self.requester)

    def get_view_by_url(self, str_view_url):
        # for nested view
        str_view_name = str_view_url.split('/view/')[-1].replace('/', '')
        return View(str_view_url, str_view_name, jenkins_obj=self)

    def has_view(self, view_path):
        return (view_path in self.views)

    def update_job(self, jobname, config):
        """Update a job

        :param jobname: name of job, str
        :param config: new configuration of job, xml
        :return: updated Job obj
        """
        if self.has_job(jobname):
            self.requester.post_xml_and_confirm_status(
                '%s/job/%s/config.xml' % (self.baseurl, jobname), data=config)
            self.poll()
            if (not self.has_job(jobname) and
                    self.jobs[jobname].get_config() != config):
                raise JenkinsAPIException('Cannot update job %s' % jobname)
        else:
            raise UnknownJob(jobname)
        return self[jobname]

    @property
    def views(self):
        return Views(self)

    def get_jobs_info(self):
        jobs = self.poll(tree='jobs[name,url,color]')['jobs']
        for info in jobs:
            yield info['url'], info['name']

    def get_job_config(self, url):
        response = self.requester.get_and_confirm_status(url + '/config.xml')
        return response.text
