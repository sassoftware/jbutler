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


import re


VERSION = "1.0.0"  # jbutler version

VIEW_SEP = '/'  # character used to separate view path elements

YAML_KWARGS = {  # default args to yaml
    'default_flow_style': False,
    }

YES = ('y', 'Y', '')  # characters that represent a yes answer

NO = ('n', 'N')  # characters that represent a no answer

QUIT = ('q', 'Q')  # characters that represent a quit answer

MACRO_RE = re.compile(r'%\(\w+\)s')  # regular expression to mactch macros
