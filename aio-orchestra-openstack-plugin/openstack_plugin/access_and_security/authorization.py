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

from openstack_plugin.common import clients

from aiorchestra.core import utils

AUTH_PROPERTIES = 'auth_properties'
TOKEN = 'auth_token'


@utils.operation
async def authorize(node, inputs):
    node.context.logger.info(
        '[{0}] - Attempting to authorize '
        'in OpenStack.'.format(node.name))
    keystone = clients.openstack.keystone(node)
    node.update_runtime_properties(AUTH_PROPERTIES, node.properties)
    node.update_runtime_properties(TOKEN, keystone.auth_token)


@utils.operation
async def inject(source, target, inputs):
    source.context.logger.info(
        "[{0} -----> {1}] - Establishing relationship."
        .format(target.name, source.name))
    for rAttr in [AUTH_PROPERTIES, TOKEN]:
        if rAttr in target.runtime_properties:
            source.update_runtime_properties(
                rAttr, target.runtime_properties.get(rAttr))


@utils.operation
async def eject(source, target, inputs):
    source.context.logger.info(
        "[{0} --X--> {1}] - Breaking relationship."
        .format(target.name, source.name))
    source.context.logger.info('Injecting attributes to node "{0}".'
                               .format(source.name))
    for rAttr in [AUTH_PROPERTIES, TOKEN]:
        if rAttr in source.runtime_properties:
            del source.runtime_properties[rAttr]
