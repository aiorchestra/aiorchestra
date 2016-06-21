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


class TestContextLoader(base.BaseAIOrchestraTestCase):

    def setUp(self):
        super(TestContextLoader, self).setUp()

    def tearDown(self):
        super(TestContextLoader, self).tearDown()

    @base.with_template('simple_node_template.yaml')
    def test_context_builder(self, template_path):
        context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG)

    @base.with_template('simple_node_template.yaml')
    def test_deployment_plan(self, template_path):
        _c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG)
        self.assertIsNotNone(_c.deployment_plan)

    @base.with_template('simple_node_template.yaml')
    def test_nodes_in_deployment_plan_presence(self, template_path):
        _c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG)
        self.assertIsNotNone(_c.deployment_plan)
        for node in _c.nodes:
            self.assertIn(node, _c.deployment_plan)

    @base.with_template('simple_node_template.yaml')
    def test_relationship_presence(self, template_path):
        _c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG)
        plan = _c.deployment_plan
        node_deps_plan = plan[_c.node_from_name('dependent_node')]
        self.assertIn(_c.node_from_name('test_node'), node_deps_plan)

    @base.with_template('simple_node_template.yaml')
    def test_relationship_presense_for_node_itself(self, template_path):
        _c = context.OrchestraContext(
            'simple_node_template',
            path=template_path,
            logger=base.LOG)
        plan = _c.deployment_plan
        node_deps_plan = plan[_c.node_from_name('test_node')]
        self.assertIn(_c.node_from_name('test_node'), node_deps_plan)
