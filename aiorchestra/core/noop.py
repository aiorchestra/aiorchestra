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
async def noop(*args, **kwargs):
    pass


@utils.operation
async def link(source, target, inputs):
    source.context.logger.debug(
        '[{0} {2} {1}] - Relationship implementation was not '
        'found, using stab for "{3}" event.'
        .format(target.name, source.name, '----->', 'link'))
    source.batch_update_runtime_properties(**target.runtime_properties)


@utils.operation
async def unlink(source, target, inputs):
    source.context.logger.debug(
        '[{0} {2} {1}] - Relationship implementation was not '
        'found, using stab for "{3}" event.'
        .format(target.name, source.name, '--X-->', 'unlink'))
    for k in target.runtime_properties:
        if k in source.runtime_properties:
            del source.runtime_properties[k]
