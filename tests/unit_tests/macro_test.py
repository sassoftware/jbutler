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

from jbutler import macros

from .. import base


class MacroTests(base.JbutlerTestCase):
    """Test the macro module"""
    def test_setitem(self):
        m = macros.Macros()
        self.assertFalse('key' in m)

        m['key'] = 'value'
        self.assertTrue('key' in m)
        self.assertEqual('value', m._store['key'])

    def test_getitem(self):
        m = macros.Macros(key='value')
        self.assertEqual('value', m['key'])
        self.assertEqual('value', m.get('key'))

        m = macros.Macros(key='value', other='%(key)s')
        self.assertEqual('value', m['other'])
        self.assertEqual('value', m.get('other'))

    def test_delitem(self):
        m = macros.Macros(key='value', other='%(key)s')
        self.assertEqual('value', m['other'])

        del m['key']
        self.assertEqual('%(key)s', m['other'])
