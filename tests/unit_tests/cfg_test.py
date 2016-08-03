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

from jbutler.lib import cfg

from ..import base


class CfgTestCase(base.JbutlerTestCase):
    """Test the cfg module of jbutler"""
    def test_defaults(self):
        config = cfg.JbutlerConfigParser()
        self.assertEqual('jobs', config.jobdir)
        self.assertEqual('templates', config.templatedir)
        self.assertTrue(config.ssl_verify)

    def test_no_server(self):
        self.mkfile('noserver', contents='\n')
        config = cfg.JbutlerConfigParser()
        with self.assertRaises(cfg.MissingRequiredOptionError) as cm:
            config.read(['noserver'])
            self.assertIn("'server'", str(cm.exception))
