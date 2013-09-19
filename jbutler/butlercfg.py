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
Implements an ButlerConfiguration object, which is similar to
a C{conarycfg} object.
"""
import base64
import os

from conary.lib import cfg
from conary.lib import cfgtypes


#pylint: disable-msg=R0904
# R0904: Too many public methods

class CfgPassword(cfgtypes.CfgType):
    """
    Obscured password
    """
    def parseString(self, val):
        assert val, "expected password"
        return base64.b64encode(val)

    def format(self, val, displayOptions=None):
        if val is None:
            val = ''
        elif displayOptions.get('hidePasswords'):
            return '<password>'
        else:
            return base64.b64decode(val)


class ButlerConfiguration(cfg.ConfigFile):
    """
    This is the base object for vapp-butler configuration.
    """
    server = cfgtypes.CfgString
    username = cfgtypes.CfgString
    password = CfgPassword

    def __init__(self, readConfigFiles=False, ignoreErrors=False, root=''):
        cfg.ConfigFile.__init__(self)
        if hasattr(self, 'setIgnoreErrors'):
            self.setIgnoreErrors(ignoreErrors)
        if readConfigFiles:
            self.readFiles(root=root)

        self._externalPassword = False

    def readFiles(self, root=''):
        """
        Populate this configuration object with data from all
        standard locations for vapp-butler configuration files.
        @param root: if specified, search for config file under the given
        root instead of on the base system.  Useful for testing.
        """
        self.read(root + '/etc/jbutlerrc', exception=False)
        if 'HOME' in os.environ:
            self.read(root + os.environ["HOME"] + "/" + ".jbutlerrc",
                      exception=False)
        self.read('jbutlerrc', exception=False)
