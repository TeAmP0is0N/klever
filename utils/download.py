#!/usr/bin/env python3
#
# Copyright (c) 2014-2016 ISPRAS (http://www.ispras.ru)
# Institute for System Programming of the Russian Academy of Sciences
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

from utils import get_args_parser, Session

parser = get_args_parser('Job with specified identifier download.')
parser.add_argument('identifier', help='Job identifier')
parser.add_argument('-o', '--out', help='Downloaded archive name')
args = parser.parse_args()

with Session(args) as session:
    arch = session.download_job(args.identifier, args.out)
print('\nJob archive was successfully saved to {0}'.format(arch))