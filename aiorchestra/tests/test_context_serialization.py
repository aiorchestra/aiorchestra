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


class TestContextSerialization(base.BaseAIOrchestraTestCase):

    def setUp(self):
        super(TestContextSerialization, self).setUp()

    def tearDown(self):
        super(TestContextSerialization, self).tearDown()

    @base.with_deployed('template_with_plugin.yaml', do_deploy=True)
    def test_context_serialized(self, context):
        serialized_context = context.serialize()
        self.assertIsInstance(serialized_context, dict)
        self.assertIn('nodes', serialized_context)
        self.assertIn('status', serialized_context)
        self.assertIn('name', serialized_context)

    @base.with_deployed('template_with_plugin.yaml', do_deploy=False)
    def test_context_deserialized(self, context):
        serialized_context = context.serialize()
        new_context = self.deserialize_context(serialized_context)
        self.assertEqual(context.name, new_context.name)
        self.assertEqual(context.status, new_context.status)

    @base.with_deployed('template_with_plugin.yaml', do_deploy=False)
    def test_context_serialized_before_and_after(self, context):
        serialized_context = context.serialize()
        new_context = self.deserialize_context(serialized_context)
        context.run_deploy()
        self.assertEqual(context.name, new_context.name)
        self.assertNotEqual(context.status, new_context.status)
        context.run_undeploy()
        serialized_context = context.serialize()
        new_context = self.deserialize_context(serialized_context)
        self.assertEqual(context.status, new_context.status)

    @base.with_deployed('template_with_plugin.yaml', do_deploy=True)
    def test_nodes_were_provisioned_after_deploy(self, context):
        self.assertTrue(context._assert_nodes_were_provisioned())

    @base.with_deployed('template_with_plugin.yaml', do_deploy=False)
    def test_nodes_were_provisioned_before_deploy(self, context):
        self.assertFalse(context._assert_nodes_were_provisioned())
