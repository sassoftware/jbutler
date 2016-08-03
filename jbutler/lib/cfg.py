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
from six.moves import configparser
from six.moves.configparser import Error


class InvalidSectionError(Error):
    """Raised when an invalid section name is found"""

    def __init__(self, sections, source=None, lineno=None):
        msg = [repr(s) for s in sections if s != 'jbutler']
        if source is not None:
            message = ['While reading from', repr(source)]
            if lineno is not None:
                message.append(' line {0:2d}'.fromat(lineno))
            message.append(': invalid sections ')
            message.extend(msg)
            msg = message
        else:
            msg.insert(0, 'Invalid sections: ')
        Error.__init__(''.join(msg))
        self.sections = sections
        self.source = source
        self.lineno = lineno
        self.args = (sections, source, lineno)


class MissingRequiredOptionError(Error):
    """Raised when a required option is not defined"""

    def __init__(self, option):
        Error.__init__(self, u"Missing required option %r" % option)
        self.option = option
        self.args = (option, )


class JbutlerConfigParser(object):
    """A jbutler configuration object"""
    _cfg = None
    section = 'jbutler'
    options = dict(server=(dict(required=True)),
                   username=dict(default=''),
                   password=dict(default=''),
                   ssl_verify=dict(type=bool, default='true'),
                   jobdir=dict(default='jobs'),
                   templatedir=dict(default='templates'),
                   )

    def __init__(self):
        self._cfg = configparser.SafeConfigParser()
        self._cfg.add_section(self.section)

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(u"'{0}' object has no attribute '{1}'".format(
                                 self.__class__.__name__, name))
        if hasattr(self._cfg, name):
            return getattr(self._cfg, name)
        return self.get(name)

    def __setattr__(self, name, value):
        if name in self.options:
            return self.set(name, value)
        return super(JbutlerConfigParser, self).__setattr__(name, value)

    def _get_option_config(self, option, raise_exception=True):
        try:
            return self.options[option]
        except KeyError:
            if raise_exception:
                raise TypeError(u"Unkown config option %r" % option)

    def _validate_value(self, option, value, raise_exception=True):
        try:
            self._get_option_config(option)
        except TypeError:
            if raise_exception:
                raise
        else:
            cfg_type = self.options[option].get('type', str)
            if isinstance(value, cfg_type):
                return True
        if raise_exception:
            raise TypeError(u"Option '%s' must be of type %s" %
                            (option, cfg_type))
        return False

    def items(self, raw=False, vars=None):
        return self._cfg.items('jbutler', raw=raw, vars=vars)

    def get(self, option, *args, **kwargs):
        option_config = self._get_option_config(option)
        type = option_config.get('type', str)
        if not self._cfg.has_option(self.section, option):
            if not option_config.get('required'):
                return option_config.get('default')
            raise configparser.NoOptionError(option, self.section)
        if type == str:
            return self._cfg.get(self.section, option, *args, **kwargs)
        elif type == int:
            return self._cfg.getint(self.section, option, *args, **kwargs)
        elif type == float:
            return self._cfg.getfloat(self.section, option, *args, **kwargs)
        elif type == bool:
            return self._cfg.getboolean(self.section, option, *args, **kwargs)

    def read(self, filenames):
        self._cfg.read(filenames)
        invalid = [s for s in self._cfg.sections() if s != self.section]
        if invalid:
            raise InvalidSectionError(invalid)

        options = self._cfg.options(self.section)
        for name, config in self.options.items():
            if config.get('required') and name not in options:
                raise MissingRequiredOptionError(name)

    def set(self, option, value):
        self._validate_value(option, value)
        self._cfg.set(self.section, option, value)

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        fp.write('[{0}]\n'.format(self.section))
        for option in sorted(self.options.keys()):
            value = str(self.get(option, raw=True)).replace('\n', '\n\t')
            fp.write('{0} = {1}\n'.format(option, value))


def get_config(config_files, **kwargs):
    """Get a config object

    The config object will be initialized from the files listed in
    ``config_files``, with overrides passed in as keyword arguments.

    :param list config_files: a list of paths to read configuration from
    :param str server: URL of jenkins master
    :param str username: username to use for authentication
    :param str password: password to use for authentication
    :param bool ssl_verify: whether to verify the server's ssl certificate
    :param str jobdir: name of directory to store job configurations in,
                       relative to the project directory (default: jobs)
    :param str templatedir: name of directory to store template files in,
                            relative to the project directory
                            (default: templates)
    """
    cfg = JbutlerConfigParser()
    cfg.read(config_files)
    for k, v in kwargs.items():
        cfg.set(k, v)
    return cfg
