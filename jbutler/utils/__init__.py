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

import yaml

from . import lxml_utils
from ..constants import YAML_KWARGS


def readJob(filename):
    with open(filename) as fh:
        return lxml_utils.parse(fh)


def readTemplate(filename):
    with open(filename) as fh:
        return yaml.safe_load(fh)


def writeJob(filename, data):
    with open(filename, 'wb') as fh:
        fh.write(lxml_utils.tostring(data))


def writeTemplate(filename, data):
    with open(filename, 'w') as fh:
        yaml.safe_dump(data, fh, **YAML_KWARGS)
