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
jenkins-butler specific errors
"""


class JButlerBaseError(RuntimeError):
    """
    Base class for all jenkins-butler exceptions.

    New exceptions should derive from a subclass of this one, for
    example JButlerCommandError.

    :cvar template: A template string used when displaying the
                    exception. Must use only keyword substitution.
    """
    template = None

    def __init__(self, *args, **kwargs):
        if self.template is None:
            super(JButlerBaseError, self).__init__(*args, **kwargs)
        else:
            super(JButlerBaseError, self).__init__(
                self.template.format(*args, **kwargs))


class JButlerInternalError(JButlerBaseError):
    """
    superclass for all errors that are not meant to be seen.

    Errors deriving from InternalError should never occur, but when they do
    they indicate a failure within the code to handle some unexpected case.

    Do not raise this exception directly.
    """


class CommandError(JButlerBaseError):
    """jbutler command errors"""
    pass


class TemplateError(JButlerBaseError):
    pass


class SerializationError(JButlerBaseError):
    """error in expected serialized data"""
    template = 'Malformed serialized data: {key} : {value}'
