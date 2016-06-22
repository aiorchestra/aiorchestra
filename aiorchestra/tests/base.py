#    Author: Denys Makogon
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import asyncio
import os
import uvloop

import testtools

from aiorchestra.core import logger


LOG = logger.UnifiedLogger(
    log_to_console=True,
    level=os.environ.get('AIORCHESTRA_LOG_LEVEL', 'INFO')
).setup_logger(__name__)


def with_template(template_name):
    def action_wrapper(action):
        def wraps(*args, **kwargs):
            self = list(args)[0]
            path = os.path.join(self.tosca_directory, template_name)
            new_args = list(args)
            new_args.append(path)
            return action(*new_args, **kwargs)
        return wraps
    return action_wrapper


class BaseAIOrchestraTestCase(testtools.TestCase):
    tosca_directory = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'templates')

    def setUp(self):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.event_loop = asyncio.new_event_loop()
        super(BaseAIOrchestraTestCase, self).setUp()

    def tearDown(self):
        self.event_loop.close()
        super(BaseAIOrchestraTestCase, self).tearDown()
