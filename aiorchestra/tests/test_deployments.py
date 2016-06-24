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

from aiorchestra.core import context

from aiorchestra.tests import base


class TestDeployments(base.BaseAIOrchestraTestCase):

    def setUp(self):
        super(TestDeployments, self).setUp()

    def tearDown(self):
        super(TestDeployments, self).tearDown()

    @base.with_template('simple_node_template.yaml')
    def test_deploy_status_before_deploy(self, template_path):
        c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG,
            event_loop=self.event_loop)
        self.assertEqual(c.status, context.OrchestraContext.PENDING)

    @base.with_template('simple_node_template.yaml')
    def test_deploy_status_after_deploy(self, template_path):
        c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG,
            event_loop=self.event_loop)
        c.run_deploy()
        self.assertEqual(c.status, context.OrchestraContext.COMPLETED)

    @base.with_template('simple_node_template.yaml')
    def test_undeploy_error(self, template_path):
        c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG,
            event_loop=self.event_loop)
        self.assertRaises(Exception, c.run_undeploy)

    @base.with_template('simple_node_template.yaml')
    def test_deploy_error(self, template_path):
        c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG,
            event_loop=self.event_loop)
        c.status = context.OrchestraContext.FAILED
        self.assertRaises(Exception, c.run_deploy)

    @base.with_template('simple_node_template.yaml')
    def test_undeploy_twice(self, template_path):
        c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG,
            event_loop=self.event_loop)
        c.run_deploy()
        c.run_undeploy()
        self.assertRaises(Exception, c.run_undeploy)

    @base.with_deployed('invalid_node_template.yaml', do_deploy=False)
    def test_unable_to_import_lifecycle_implementation(self, c):
        ex = self.assertRaises(Exception, c.run_deploy)
        self.assertIn("No module named 'module'", str(ex))

    @base.with_deployed('invalid_node_template-2.yaml', do_deploy=False)
    def test_invalid_node_event_implementation_reference(self, c):
        ex = self.assertRaises(Exception, c.run_deploy)
        self.assertIn('Invalid event implementation reference', str(ex))
