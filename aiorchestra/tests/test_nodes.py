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

from aiorchestra.tests import base


class TestContextNodes(base.BaseAIOrchestraTestCase):

    def setUp(self):
        super(TestContextNodes, self).setUp()

    def tearDown(self):
        super(TestContextNodes, self).tearDown()

    @base.with_deployed('simple_node_template.yaml')
    def test_nodes(self, context):
        self.assertEqual(2, len(context.nodes))

    @base.with_deployed('simple_node_template.yaml')
    def test_nodes_has_parents(self, context):
        node = context.node_from_name('dependent_node')
        self.assertTrue(node.has_parents)

    @base.with_deployed('simple_node_template.yaml')
    def test_nodes_parent_presence(self, context):
        node = context.node_from_name('dependent_node')
        self.assertIn('test_node', node.parent_nodes)
