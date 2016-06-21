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


@utils.operation
async def create(node, inputs):
    use_existing = node.properties['use_existing']
    name = node.properties['name']
    nova = clients.openstack.nova(node)
    if not use_existing:
        pub_key = node.properties.get('public_key')
        keypair = nova.keypairs.create(name, public_key=pub_key)
    else:
        node.context.logger.info(
            '[{0}] - Using existing keypair with name "{1}".'
            .format(node.name, name))
        keypair = nova.keypairs.get(node.properties['name'])

    node.batch_update_runtime_properties(**{
        'private_key_content': (
            keypair.private_key if not use_existing else None),
        'id': keypair.id,
        'public_key': keypair.public_key,
        'name': name,
    })


@utils.operation
async def delete(node, inputs):
    try:
        use_existing = node.properties['use_existing']
        if not use_existing:
            nova = clients.openstack.nova(node)
            nova.keypairs.delete(node.properties['name'])
        else:
            node.context.logger.info('Skipping delete operation '
                                     'for node "{0}" because it '
                                     'is external resource.'
                                     .format(node.name))
    except Exception as ex:
        node.context.logger.error(str(ex))
        raise ex


@utils.operation
async def link_to_compute(source, target, inputs):
    source.context.logger.info(
        "[{0} -----> {1}] - Establishing relationship."
        .format(target.name, source.name))
    source.update_runtime_properties({
        'ssh_keypair': target.runtime_properties
    })


@utils.operation
async def unlink_to_compute(source, target, inputs):
    source.context.logger.info(
        "[{0} --X--> {1}] - Breaking relationship."
        .format(target.name, source.name))
    if 'ssh_keypair' in source.runtime_properties:
        del source.update_runtime_properties['ssh_keypair']
