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


class TestPlugin(base.BaseAIOrchestraTestCase):

    def setUp(self):
        super(TestPlugin, self).setUp()

    def tearDown(self):
        super(TestPlugin, self).tearDown()

    @base.with_deployed('template_with_plugin.yaml', do_deploy=True)
    def test_node_operation_after_deploy(self, context):
        nodes = context.nodes
        for event_mark in ['created', 'configured', 'started']:
            for node in nodes:
                self.assertIn(event_mark, node.runtime_properties)

    @base.with_deployed('template_with_plugin.yaml', do_deploy=False)
    def test_node_operation_before_deploy(self, context):
        nodes = context.nodes
        for event_mark in ['created', 'configured', 'started']:
            for node in nodes:
                self.assertNotIn(event_mark, node.runtime_properties)

    @base.with_deployed('template_with_plugin.yaml', do_deploy=False)
    def test_node_operation_after_undeploy(self, context):
        nodes = context.nodes
        for node in nodes:
            self.assertEqual({}, node.runtime_properties)

    @base.with_deployed('template_with_plugin.yaml', do_deploy=True)
    def test_link_relationship_after_deploy(self, context):
        parent = context.node_from_name('test_node')
        child = context.node_from_name('dependent_node')
        self.assertIn('source', parent.runtime_properties)
        self.assertIn('target', child.runtime_properties)
        source_name = parent.runtime_properties['source']
        target_name = child.runtime_properties['target']
        self.assertEqual(parent.name, target_name)
        self.assertEqual(child.name, source_name)

    @base.with_deployed('template_with_bad_plugin.yaml', do_deploy=False)
    def test_plugin_operations_should_be_coroutines(self, context):
        ex = self.assertRaises(Exception, context.run_deploy)
        self.assertIn("object NoneType can't be used in "
                      "'await' expression", str(ex))

    @base.with_deployed('simple_template_for_rollback_test.yaml',
                        do_deploy=True, enable_rollback=True)
    def test_rollback(self, context):
        pass
