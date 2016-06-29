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

from aiorchestra.core import utils


@utils.operation
async def create(node, inputs):
    node.context.logger.info('[{0}] - Created.'.format(node.name))
    node.batch_update_runtime_properties(**{
        'created': True,
        'name': node.name,
        'context_name': node.context.name,
        'context_status': node.context.status,
    })


@utils.operation
async def start(node, inputs):
    node.context.logger.info('[{0}] - Started.'.format(node.name))
    node.batch_update_runtime_properties(**{
        'started': True,
    })


@utils.operation
async def fail_start(node, inputs):
    node.context.logger.info('[{0}] - Now i will raise exception '
                             'and rollback should work.'
                             .format(node.name))
    raise Exception('i must fail.')


@utils.operation
async def stop(node, inputs):
    node.context.logger.info('[{0}] - Stopped.'.format(node.name))
    node.batch_update_runtime_properties(**{
        'stopped': False,
    })


@utils.operation
async def delete(node, inputs):
    node.context.logger.info('[{0}] - Deleted.'.format(node.name))
    node.batch_update_runtime_properties(**{
        'deleted': True,
    })


@utils.operation
async def configure(node, inputs):
    node.context.logger.info('[{0}] - Configured.'.format(node.name))
    node.batch_update_runtime_properties(**{
        'configured': True,
    })


@utils.operation
async def link(source, target, inputs):
    source.update_runtime_properties('target', target.name)
    target.update_runtime_properties('source', source.name)
    source.batch_update_runtime_properties(**target.runtime_properties)


@utils.operation
async def unlink(source, target, inputs):
    if 'target' in source.runtime_properties:
        del source.runtime_properties['target']
    for k in target.runtime_properties:
        if k in source.runtime_properties:
            del source.runtime_properties[k]
    if 'target' in target.runtime_properties:
        del target.runtime_properties['target']


@utils.operation
def is_not_coroutine(node, inputs):
    pass
