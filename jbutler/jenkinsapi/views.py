#
# Copyright (c) SAS Institute Inc.
#


from jenkinsapi.views import Views as _Views

from jbutler.jenkinsapi.view import View


class Views(_Views):
    def __getitem__(self, view_name):
        for row in self.jenkins._data.get('views', []):
            if row['name'] == view_name:
                return View(
                    row['url'],
                    row['name'],
                    self.jenkins)
        else:
            return None

    def iteritems(self):
        """
        Get the names & objects for all views
        """
        self.jenkins.poll()
        for row in self.jenkins._data.get('views', []):
            name = row['name']
            url = row['url']

            yield name, View(url, name, self.jenkins)
