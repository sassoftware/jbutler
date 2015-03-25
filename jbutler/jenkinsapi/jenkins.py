#
# Copyright (c) SAS Institute Inc.
#


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
        #for nested view
        str_view_name = str_view_url.split('/view/')[-1].replace('/', '')
        return View(str_view_url, str_view_name, jenkins_obj=self)

    def has_view(self, view_path):
        return (view_path in self.views)

    def update_job(self, jobname, config):
        """
        Update a job
        :param jobname: name of job, str
        :param config: new configuration of job, xml
        :return: updated Job obj
        """
        if self.has_job(jobname):
            if isinstance(config, unicode):
                config = str(config)
            self.requester.post_xml_and_confirm_status(
                '%s/job/%s/config.xml' % (self.baseurl, jobname), data=config)
            self.poll()
            if (not self.has_job(jobname)
                    and self.jobs[jobname].get_config() != config):
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
            yield info["url"], info["name"]

