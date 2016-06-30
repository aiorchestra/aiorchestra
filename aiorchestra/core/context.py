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
import collections
import uvloop

from toscaparser import tosca_template

from aiorchestra.core import node
from aiorchestra.core import logger as log


class OrchestraContext(object):

    (PENDING, RUNNING, COMPLETED, FAILED) = ('pending', 'running',
                                             'completed', 'failed')
    AVAILABLE_FOR_DESTRUCTION = [COMPLETED, FAILED]

    def __init__(self, name, path=None,
                 template_inputs=None,
                 logger=None,
                 event_loop=None,
                 enable_rollback=False):
        self.__name = name
        self._tmplt = tosca_template.ToscaTemplate(path=path, a_file=True)
        self.__path = path
        self.origin_nodes = self._tmplt.graph.nodetemplates
        self.vertices = self._tmplt.graph.vertices
        self.inputs_definitions = self._tmplt.inputs
        self.__outputs = self._tmplt.outputs
        self.template_inputs = template_inputs if template_inputs else {}
        self.__status = self.PENDING
        if not logger:
            self.logger = log.UnifiedLogger(
                log_to_console=True,
                level="DEBUG").setup_logger(__name__)
        else:
            self.logger = logger
        if not event_loop:
            uv_loop = uvloop.new_event_loop()
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            asyncio.set_event_loop(uv_loop)
            self.event_loop = asyncio.get_event_loop()
        else:
            self.event_loop = event_loop
        self.__orchestra_nodes = [node.OrchestraNode(self, origin_node)
                                  for origin_node in self.origin_nodes]
        self.__deployment_plan = None
        self.rollback_enabled = enable_rollback

    @property
    def outputs(self):
        outputs = {}
        if self.status in self.AVAILABLE_FOR_DESTRUCTION:
            for item in self.__outputs:
                if hasattr(item.value, 'node_template_name'):
                    orchestra_node = self.node_from_name(
                        item.value.node_template_name)
                    value = orchestra_node.process_output(item)
                else:
                    value = item.value
                outputs.update({item.name: value})
        else:
            msg = ('Unable to process outputs, deployment is not in '
                   'appropriate status, current: "{0}".'.format(self.status))
            self.logger.error(msg)
            raise Exception(msg)
        return outputs

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        self.__status = status

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, other):
        raise Exception('Orchestra context name is unique. '
                        'Current - {0}.'.format(self.name))

    @property
    def nodes(self):
        return self.__orchestra_nodes

    @nodes.setter
    def nodes(self, new):
        self.__orchestra_nodes = new

    def node_from_name(self, name):
        for orchestra_node in self.nodes:
            if orchestra_node.name == name:
                return orchestra_node

    def __setup_deployment_plan(self):
        self.logger.info('Retrieving deployment plan for '
                         'TOSCA template {0} context.'
                         .format(self.name))

        deps_by_node = collections.defaultdict(list)
        deps = []

        def recursive_dependency_collector(_node):
            _node.attempt_to_validate()
            _deps = []
            if _node.has_parents:
                if _node not in deps:
                    deps.append(_node)
                for other_required_by in sorted(_node.parent_nodes):
                    next_node = self.node_from_name(other_required_by)
                    _deps.append(
                        recursive_dependency_collector(next_node))
                return
            deps.append(_deps if _deps else _node)
            return

        for orchestra_node in self.nodes:
            self.logger.debug('Retrieving deployment dependencies '
                              'and building deployment task sequence for '
                              'node {0} of TOSCA template {1} context.'
                              .format(orchestra_node.name, self.name))
            recursive_dependency_collector(orchestra_node)
            deps = list(reversed(deps))
            filtered = []
            for dep in deps:
                if dep.name not in [n.name for n in filtered]:
                    filtered.append(dep)
            deps_by_node[orchestra_node] = filtered
            self.logger.debug('Node {0} has "{1}" deployment task sequence.'
                              .format(orchestra_node.name, ", "
                                      .join([str(n) for n in filtered])))
            deps = []

        d = collections.OrderedDict()
        deps_by_node_new = sorted(
            deps_by_node, key=lambda k: len(deps_by_node[k]))
        for item in deps_by_node_new:
            d[item] = deps_by_node[item]
        self.__deployment_plan = d

    @property
    def deployment_plan(self):
        if self.__deployment_plan is None:
            self.__setup_deployment_plan()
        return self.__deployment_plan

    def _gather_events(self, event):
        sequenced_events = []
        nodes_order = []
        for target_node, deployment_plan in self.deployment_plan.items():
            for node_template in deployment_plan:
                if node_template not in nodes_order:
                    nodes_order.append(node_template)
        for node_template in nodes_order:
            event_coroutine = getattr(node_template, event)
            sequenced_events.append(event_coroutine())
        return sequenced_events

    def _assert_nodes_were_provisioned(self):
        gather = []
        for n in self.nodes:
            self.logger.debug('Node "{0}" is provisioned: "{1}".'
                              .format(n.name, n.is_provisioned))
            gather.append(n.is_provisioned)
        return any(gather)

    async def deploy(self):
        task_list = []
        standard_events_order = ['create', 'configure', 'start']
        self.logger.info('Starting deployment process for deployment '
                         'context {0}.'.format(self.name))
        if self.status == self.PENDING:
            for event in standard_events_order:
                task_list.extend(self._gather_events(event))
            try:
                self.status = self.RUNNING
                for coro in task_list:
                    await coro
                self._assert_nodes_were_provisioned()
                self.status = self.COMPLETED
            except Exception as ex:
                self.status = self.FAILED
                if not self.rollback_enabled:
                    raise ex
                else:
                    self.logger.info('Rollback enabled, no need '
                                     'to raise exception.')
            self.logger.info('Deployment "{0}" finished'
                             ' with status "{1}".'
                             .format(self.name, self.status))
        else:
            raise Exception('Unable to run deployment. '
                            'PENDING status required.')

    async def undeploy(self):
        self.logger.info('Starting teardown process for deployment '
                         'context {0}.'.format(self.name))
        task_list = []
        standard_events_order = ['delete', 'stop']
        for event in standard_events_order:
            task_list.extend(self._gather_events(event))
        is_able = (self.status in self.AVAILABLE_FOR_DESTRUCTION if
                   not self.rollback_enabled else self.rollback_enabled)
        if is_able:
            self.logger.info('Destroying deployment {0}'.format(self.name))
            if not self._assert_nodes_were_provisioned():
                msg = ('Unable to destroy deployment "{0}" because of the '
                       'nodes was not provisioned'.format(self.name))
                self.logger.error(msg)
                raise Exception(msg)
            try:
                for coro in reversed(task_list):
                    await coro
                self.logger.info('Deployment "{0}" destroyed.'
                                 .format(self.name))
            except Exception as ex:
                self.logger.error('Failed to destroy deployment. '
                                  'Reason: "{0}".'.format(str(ex)))
                raise ex
            finally:
                self._assert_nodes_were_provisioned()
                self.status = self.PENDING
        else:
            msg = ('Unable to delete deployment because it '
                   'is not in appropriate status, current "{0}".'
                   .format(self.status))
            raise Exception(msg)

    def run_deploy(self):
        self.event_loop.run_until_complete(self.deploy())

    def run_undeploy(self):
        self.event_loop.run_until_complete(self.undeploy())

    def serialize(self):
        return {
            'name': self.__name,
            'status': self.status,
            'template_inputs': self.template_inputs,
            'nodes': [n.serialize() for n in self.nodes],
            'path': self._tmplt.path
        }

    @classmethod
    def load(cls, logger, event_loop=None, **kwargs):
        name = kwargs.get('name')
        inputs = kwargs.get('template_inputs')
        nodes = kwargs.get('nodes')
        __status = kwargs.get('status')
        path = kwargs.get('path')
        context = cls(name,
                      path=path,
                      template_inputs=inputs,
                      event_loop=event_loop,
                      logger=logger)
        context.status = __status
        _ns = []
        for ser_n in nodes:
            _node = context.node_from_name(ser_n['__name'])
            _node.load(**ser_n)
            _ns.append(_node)
        context.nodes = _ns
        context.__setup_deployment_plan()
        return context
