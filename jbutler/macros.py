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
import collections
import re

MACRO_RE = re.compile(r'%\((\w+)\)s')  # regular expression to mactch macros


class Macros(collections.MutableMapping):
    """Recursively map macros to values"""
    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)

    def __delitem__(self, key):
        del self._store[key]

    def __getitem__(self, key):
        value = self._store[key]
        m = MACRO_RE.match(value)
        if m:
            k = m.groups()[0]
            if k in self:
                value = self[k]
        return value

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __setitem__(self, key, value):
        self._store[key] = value
