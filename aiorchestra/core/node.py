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

import importlib
import sys

from toscaparser import functions

from aiorchestra.core import noop


RELATIONSHIP_STABS = {
    'link': 'aiorchestra.core.noop:link',
    'unlink': 'aiorchestra.core.noop:unlink',
}


def check_for_event_definition(action):
    def wraps(*args, **kwargs):
        self, node, event = args
        available = self.check_event_availability(event, 'Standard')
        if not available:

            def stab(*args, **kwargs):
                msg = ('Lifecycle event "{0}" was not implemented '
                       'for node "{1}". Skipping.'
                       .format(event, node.name))
                self.context.logger.debug(msg)
                return None, None

            return stab(*args, **kwargs)
        else:
            return action(*args, **kwargs)
    return wraps


def lifecycle_event_handler(action):

    undeploy_actions = ['stop', 'delete']

    async def wraps(*args, **kwargs):
        self = list(args)[0]
        self.context.logger.debug('Attempting to run {0} event for '
                                  'node {1}.'
                                  .format(action.__name__, self.name))
        try:
            if action.__name__ in undeploy_actions:
                if self.context.rollback_enabled:
                    if not self.is_provisioned:
                        self.context.logger.info(
                            '[{0}] - Unable to rollback node '
                            'because it was not provisioned.'
                            .format(self.name))
                        return await noop.noop(*args, **kwargs)
            result = action(*args, **kwargs)
            self.context.logger.debug('Event {0} finished successfully for '
                                      'node {1}.'
                                      .format(action.__name__, self.name))
            await result
        except Exception as ex:
            self.is_provisioned = False
            self.context.logger.error(str(ex))
            raise ex

    return wraps


class InterfaceOperations(object):

    def __init__(self, context, node):
        self.context = context
        self.node_type = node.type_definition
        self.interface_implementations = node.type_definition.interfaces
        self.check_required_lifecycle_events(node, 'Standard')

    def check_event_availability(self, check_event, lifecycle_type):
        return check_event in [
            event for event in
            self.interface_implementations.get(lifecycle_type)]

    def check_required_lifecycle_events(self, node, lifecycle_type):
        __current_events = node.type_definition.interfaces.get(lifecycle_type)
        if 'create' not in __current_events:
            msg = ('{0} lifecycle event "{1}" is required'
                   .format(lifecycle_type, 'create'))
            self.context.logger.error(msg)
            raise Exception(msg)
        if 'delete' not in __current_events:
            msg = ('{0} lifecycle event "delete" was not defined. '
                   'No way to delete provisioned node "{1}" instance.'
                   .format(lifecycle_type, node.name))
            self.context.logger.debug(msg)

    @check_for_event_definition
    def __get_standard_event(self, node, event):
        __current_events = node.type_definition.interfaces.get(
            'Standard')
        implementation = __current_events[event]['implementation']
        inputs = __current_events[event].get('inputs', {})
        if 'interfaces' in node.node.entity_tpl:
            node_events = node.node.entity_tpl[
                'interfaces']['Standard']
            if event in node_events:
                node_event = node_events[event]
                template_inputs = node_event.get('inputs', {})
                implementation = node_event.get('implementation')
                inputs.update(template_inputs)
        return implementation, inputs

    def __get_relationship_entity(self, target, source):
        relationship_events = {n.name: rel.type
                               for n, rel in source.node.related.items()}
        _required_nodes = [list(node.values())[0]
                           for node in source.node._requirements]
        rel_mapping = {}
        for _req in _required_nodes:
            if isinstance(_req, str):
                rel_mapping[_req] = relationship_events[_req]
            elif isinstance(_req, dict):
                rel_mapping[_req['node']] = _req['relationship']

        return rel_mapping.get(target.name)

    def __get_relationship_event(self, target, source, event):
        custom_defs = source.custom_defs
        relationship = self.__get_relationship_entity(target, source)
        if relationship in custom_defs:
            impl_def = custom_defs[relationship]['interfaces']['Configure']
            event_def = impl_def[event]
            return event_def['implementation'], event_def.get('inputs')
        else:
            return RELATIONSHIP_STABS[event], {}

    def import_task_method(self, impl, event, node):
        if impl:
            parts = impl.split(":")
            if len(parts) != 2:
                raise Exception('Invalid event implementation reference '
                                'for event "{0}" of node "{1}".'
                                .format(event, node.name))
            module, method = parts
            m = importlib.import_module(module)
            try:
                return getattr(m, method)
            except Exception as ex:
                self.context.logger.error(
                    'Unable to get node "{0}" lifecycle event "{1}" '
                    'implementation. Reason: {2}.'
                    .format(node.name, str(ex), event))
                raise ex
        else:
            msg = ('Missing node "{1}" lifecycle event "{0}" '
                   'implementation.'.format(event, node.name))
            self.context.logger.debug(msg)

    async def run_standard_event(self, node, event):
        impl, inputs = self.__get_standard_event(node, event)
        task = self.import_task_method(impl, event, node)
        if task:
            await task(node, inputs)

    async def run_relationship_event(self, target, source, event):
        impl, inputs = self.__get_relationship_event(target, source, event)
        task = self.import_task_method(impl, event, source)
        if task:
            await task(source, target, inputs)


class OrchestraNode(object):

    def __init__(self, context, node):
        """
        Create an instance of an advanved TOSCA graph node
        :param context: OrchestraContext instance
        :type context: aiorchestra.core.context.OrchestraContext
        :param node: TOSCA graph node
        :type node: toscaparser.nodetemplate.NodeTemplate
        """
        self.context = context
        self.node = node
        self.operations = InterfaceOperations(context, node)
        self.__name = node.name
        self.__properties = {}
        self.__attributes = {}
        self.__provisioned = False
        self.__runtime_properties = {}
        self.__type_defs = node.type_definition
        self.__prop_def = node._properties
        self.__node_type = node.type
        self.__node_type_def = self.__type_defs.custom_def[self.node.type]
        self.__custom_defs = self.__type_defs.custom_def

    @property
    def custom_defs(self):
        """
        Represents TOSCA graph custom type definitions

        :return: a mapping of custom data types
        :rtype: dict
        """
        return self.__custom_defs

    @property
    def node_type_definition(self):
        """
        Represents current node type definition

        :return: node type definition
        :rtype: dict
        """
        return self.__node_type_def

    @property
    def node_type(self):
        """
        Represents node type

        :return: node type
        :rtype: str
        """
        return self.__node_type

    @property
    def type_definition(self):
        """
        Return node type definition

        :return: node type definition
        :rtype: toscaparser.entity_template.EntityTemplate
        """
        return self.__type_defs

    @property
    def property_definishion(self):
        """
        Represents node properties definition

        :return: node properties
        :rtype: dict
        """
        return self.__prop_def

    def has_capability(self, capability_type):
        """
        Checks if node has capability

        :param capability_type: node capability type
        :return: weather node has capability or not
        :rtype: bool
        """
        return capability_type in [
            cap.type for cap in self.capabilities]

    @property
    def capabilities(self):
        """
        Represents node capabilities

        :return: a list of capabilities
        :rtype: list
        """
        return self.node._capabilities

    def get_capability(self, name):
        """
        Return specific node capability by its name

        :param name: capability name
        :type name: str
        :return: capability
        :rtype: dict
        """
        for cap in self.capabilities:
            if cap.name == name:
                cap_def = cap._properties
                for prop_name, prop_value in cap_def.items():
                    if functions.is_function(prop_value):
                        value = self.__process_tosca_function_result(
                            prop_value)
                        cap_def[prop_name] = value
                return cap._properties

    def __process_tosca_function_result(self, tosca_function_def_dict):
        func = functions.get_function(
            self.context._tmplt, self.node, tosca_function_def_dict)
        if isinstance(func, functions.GetInput):
            if (func.input_name in
                    self.context.template_inputs):
                value = self.context.template_inputs[
                    func.input_name]
                return value
        elif isinstance(func, functions.GetAttribute):
            ref_node = self.context.node_from_name(
                func.node_template_name)
            if ref_node.is_provisioned:
                if (func.attribute_name in
                        ref_node.attributes):
                    value = ref_node.attributes[
                        func.attribute_name]
                    return value
        elif isinstance(func, functions.GetProperty):
            ref_node = self.context.node_from_name(
                func.node_template_name)
            if func.property_name in ref_node.properties:
                value = ref_node.properties[
                    func.property_name]
                return value

    @property
    def artifacts(self):
        """
        Represents node artifacts

        :return: node artifacts
        """
        return self.node.entity_tpl.get('artifacts', [])

    def get_artifact_from_type(self, artifact_type):
        """
        Returns artifacts from type

        :param artifact_type: artifact type
        :type artifact_type: str
        :return: artifact
        :rtype: list
        """
        artifacts = []
        for artifact in self.artifacts:
            details = self.get_artifact_by_name(artifact)
            if details:
                if details['type'] == artifact_type:
                    artifacts.append(details)
        return artifacts

    # Addresses bug in parser
    # https://bugs.launchpad.net/tosca-parser/+bug/1598130
    def get_artifact_by_name(self, name):
        """
        Return artifact from its name

        :param name: artifact name
        :type name: str
        :return:
        """
        if name in self.artifacts:
            artifact = self.artifacts[name]
            for k, v in artifact.items():
                if functions.is_function(v):
                    func = functions.get_function(
                            self.context._tmplt, self.node, v)
                    del artifact[k][func.name]
                    if not isinstance(func, functions.GetInput):
                        raise Exception('[{0}] - Unsupported intrinsic '
                                        'function "{1}" for '
                                        'artifact definition.'
                                        .format(self.name, func.name))
                    value = self.context.template_inputs[
                        func.input_name]
                    artifact.update(
                        {k: value})
            return artifact

    # TODO(denismakogon): define OrchestraNodeProperties class
    def __setup_properties(self):
        self.context.logger.debug('Initializing node {0} properties.'
                                  .format(self.name))
        for input_ref in self.property_definishion:
            if input_ref.value is not None:
                self.context.logger.debug('Attempting to resolve node {0} '
                                          'properties for TOSCA functions.'
                                          .format(self.name))
                value = None
                if isinstance(input_ref.value, functions.GetInput):
                    if (input_ref.value.input_name in
                            self.context.template_inputs):
                        self.context.logger.debug(
                            'Property {0} for node {1} '
                            'was resolved by TOSCA get_input function.'
                            .format(input_ref.value.input_name, self.name))
                        value = self.context.template_inputs[
                            input_ref.value.input_name]
                    else:
                        if input_ref.required:
                            msg = 'Input {0} is required.'.format(
                                input_ref.value.input_name)
                            self.context.logger.error(msg)
                            raise Exception(msg)
                        else:
                            if input_ref.value.input_name in [
                                    i.name for i
                                    in self.context.inputs_definitions]:
                                self.context.logger.debug(
                                    'Attempting to look-up for default '
                                    'value for node "{0}" property "{1}" '
                                    'in TOSCA template input definitions'
                                    .format(self.name,
                                            input_ref.value.input_name))
                                for i in self.context.inputs_definitions:
                                    if i.name == input_ref.value.input_name:
                                        self.context.logger.debug(
                                            'Default value for node "{0}" '
                                            'property "{1}" in TOSCA template '
                                            'input definitions was found'
                                            ' - {2}.'.format(
                                                self.name,
                                                input_ref.value.input_name,
                                                str(i.default)))
                                        value = i.default
                            else:
                                msg = ('Node {0} non-required property "{1}" '
                                       'default value is None. Attempting to '
                                       'create value from input type "{2}".'
                                       .format(self.name,
                                               input_ref.value.input_name,
                                               input_ref.type))
                                self.context.logger.warn(msg)
                                try:
                                    _type = (
                                        'str' if input_ref.type == 'string'
                                        else input_ref.type)
                                    value = getattr(sys.modules[__name__],
                                                    _type)()
                                except Exception as e:
                                    msg = (
                                        'Unable to create instance of input '
                                        'type {0} for node {1}. It may appear '
                                        'that custom type was used. '
                                        'Falling back to None'
                                        .format(input_ref.type, self.name))
                                    self.context.logger.warn(msg)
                                    self.context.logger.error(str(e))
                                    value = input_ref.default
                elif isinstance(input_ref.value, (str, dict, int,
                                                  float, list, bool)):
                    self.context.logger.debug(
                        'Property {0} for node {1} '
                        'was resolved by assigned value in its definition.'
                        .format(input_ref.name, self.name))
                    value = input_ref.value
                elif isinstance(input_ref.value, functions.GetProperty):
                    ref_node = self.context.node_from_name(
                        input_ref.value.node_template_name)
                    if input_ref.value.property_name in ref_node.properties:
                        value = ref_node.properties[
                            input_ref.value.property_name]
                        self.context.logger.debug(
                            'Property {0} for node {1} was resolved by '
                            'assigned value in its definition.'
                            .format(input_ref.name, self.name))
                    else:
                        msg = ('Node {0} does not have referenced property.'
                               .format(ref_node.name))
                        self.context.logger.error(msg)
                        raise Exception(msg)
                elif isinstance(input_ref.value, functions.GetAttribute):
                    ref_node = self.context.node_from_name(
                        input_ref.value.node_template_name)
                    if ref_node.is_provisioned:
                        if (input_ref.value.attribute_name in
                                ref_node.attributes):
                            value = ref_node.attributes[
                                input_ref.value.attribute_name]
                            self.context.logger.debug(
                                'Property {0} for node {1} was resolved '
                                'by TOSCA get_attribute function.'
                                .format(input_ref.name, self.name))
                    else:
                        msg = (
                            'Unable to get node "{0}" attribute "{1}" '
                            'because node is not provisioned. Pre-deployment '
                            'validation failed because node "{2}" has TOSCA '
                            'get_attribute function usage that can be '
                            'resolved only at deployment time.'.format(
                                input_ref.value.node_template_name,
                                input_ref.value.attribute_name,
                                self.name))
                        self.context.logger.debug(msg)
                self.__properties.update(
                    {input_ref.name: value})
        self.context.logger.debug('Node "{0}" properties: {1}.'.format(
            self.name, str(self.__properties)))

    def process_output(self, node_output_definition):
        """
        Processes node outputs

        :param node_output_definition: TOSCA function def
        :type node_output_definition: toscaparser.functions.Function
        :return: node output value
        :rtype: object
        """
        if not self.is_provisioned:
            msg = 'Node "{0}" was not provisioned.'.format(self.name)
            self.context.logger.error(msg)
            raise Exception(msg)
        name = node_output_definition.value.attribute_name
        if isinstance(node_output_definition.value, functions.GetAttribute):
            if name not in self.attributes:
                msg = ('No such attribute "{0}" for node "{1}".'
                       .format(name, self.name))
                self.context.logger.error(msg)
                raise Exception(msg)
            return self.get_attribute(name)
        if isinstance(node_output_definition.value, functions.GetProperty):
            if name not in self.properties:
                msg = ('No such property "{0}" for node "{1}".'
                       .format(name, self.name))
                self.context.logger.error(msg)
                raise Exception(msg)
            return self.properties[name]

    # TODO(denismakogon): define OrchestraNodeAttributes class
    # TODO(denismakogon): define OrchestraNodeRuntimeProperties class
    def __setup_attributes_definition_for_node_instance(self):
        __attributes = list(
            self.node_type_definition.get('attributes', {}).keys())
        if not self.is_provisioned:
            msg = ('Can not validate attributes for node "{0}" '
                   'because it was not provisioned.'.format(self.name))
            self.context.logger.debug(msg)
        else:
            self.context.logger.debug(
                'Attempting to process node "{0}" '
                'attributes: {1}.'.format(
                    self.name, str(__attributes)))
            for attr in __attributes:
                if attr not in self.__runtime_properties:
                    msg = ('Node "{0}" attribute "{1}" was not '
                           'initialized during provisioning, '
                           'falling backe to None'.format(self.name, attr))
                    self.context.logger.debug(msg)
                value = self.__runtime_properties.get(attr)
                self.context.logger.debug('Node "{0}" attribute "{1}" was '
                                          'initialized with value "{2}".'
                                          .format(self.name, attr, value))
                self.__attributes.update({
                    attr: value
                })

    def attempt_to_validate(self):
        """
        Validates node using its properties and attributes

        :return:
        """
        try:
            self.context.logger.debug(
                'Validating properties for node "{0}".'.format(self.name))
            self.properties
            self.attributes
        except Exception as ex:
            self.context.logger.error(
                "Unable to validate node {0}. Reason: {1}"
                .format(self.name, str(ex)))
            raise ex

    @property
    def name(self):
        """
        Represents node name

        :return: name
        :rtype: str
        """
        return self.__name

    @property
    def is_provisioned(self):
        """
        Represents node state

        :return: state
        :rtype: bool
        """
        return self.__provisioned

    @is_provisioned.setter
    def is_provisioned(self, provisioned):
        """
        Node state setter

        :param provisioned: True/False
        """
        self.__provisioned = provisioned

    @property
    def properties(self):
        """
        Represents initialized node properties

        :return: node properties
        :rtype: dict
        """
        self.context.logger.debug('Retrieving node {0} properties.'
                                  .format(self.name))
        self.__setup_properties()
        return self.__properties

    @properties.setter
    def properties(self, other):
        """
        Property setter is not allowed to use.

        :param other: None
        :return:
        """
        raise Exception('Node "properties" are immutable.')

    def update_runtime_properties(self, attr, value):
        """
        Updates node runtime properties

        :param attr: name
        :param value: value
        :return: None
        :rtype: None
        """
        self.__runtime_properties.update({attr: value})

    def batch_update_runtime_properties(self, **kwargs):
        """
        Performs batch update for node runtime properties

        :param kwargs: runtime properties
        :type kwargs: dict
        :return:
        """
        for k, v in kwargs.items():
            self.update_runtime_properties(k, v)

    @property
    def attributes(self):
        """
        Represents node attributes

        :return: attributes
        :rtype: dict
        """
        self.__setup_attributes_definition_for_node_instance()
        return self.__attributes

    def get_attribute(self, attr):
        """
        Return node attribute if it exists otherwise raises exception

        :param attr: attribute to seek for
        :return: attribute value
        :rtype: object
        :raises unknown_attribute: AttributeError
        """
        if attr in self.attributes:
            return self.runtime_properties.get(attr)
        else:
            raise AttributeError('Unknown attribute "{0}" of node '
                                 '"{1}".'.format(attr, self.name))

    @attributes.setter
    def attributes(self, other):
        """
        Attribute setter is not allowed.

        :param other:
        :return:
        """
        raise Exception('Node attributes are immutable.')

    @property
    def runtime_properties(self):
        """
        Represents node runtime attributes

        :return: runtime attributes
        :rtype: dict
        """
        return self.__runtime_properties

    @runtime_properties.setter
    def runtime_properties(self, other):
        """
        Runtime properties setter

        :param other:
        :return:
        """
        self.__runtime_properties = other

    @property
    def has_parents(self):
        """
        Return True if node has parent nodes

        :return:
        """
        return True if len(self.child_nodes) > 0 else False

    @property
    def parent_nodes(self):
        """
        Returns a list of parent nodes

        :return: parents
        :rtype: list of str
        """
        required = []
        for node in [list(n.values())[0] for n in self.node._requirements]:
            if isinstance(node, str):
                required.append(node)
            elif isinstance(node, dict):
                required.append(node['node'])
        return required

    def get_requirement_capability(self, target):
        """
        Return node requirement capability

        :param target: target OrchestraNode instance
        :return: capability def
        :rtype: dict
        """
        cap_def = {}
        for req in self.node._requirements:
            for _, req_def in req.items():
                if isinstance(req_def, dict):
                    if req_def['node'] == target.name:
                        cap_def = req_def.get('capability',
                                              {'properties': {}})
                        del cap_def['type']
                        props = cap_def['properties']
                        for prop, value in props.items():
                            if functions.is_function(value):
                                new_value = (
                                    self.__process_tosca_function_result(
                                        value))
                                props[prop] = new_value
                        return cap_def['properties']
        return cap_def

    @property
    def has_children(self):
        """
        Returns true if node has child nodes

        :return: True/False
        :rtype: bool
        """
        return True if len(self.parent_nodes) > 0 else False

    @property
    def child_nodes(self):
        """
        Represents a list of child nodes

        :return: child nodes
        :rtype: list
        """
        return [list(req.values())[0] for req in self.node.requirements]

    @lifecycle_event_handler
    async def link(self, source):
        """
        Relationship coroutine to link target to source

        :param source:
        :return: None
        :rtype: None
        """
        await self.operations.run_relationship_event(self, source, 'link')

    @lifecycle_event_handler
    async def unlink(self, source):
        """
        Relationship coroutine to unlink target from source

        :param source:
        :return: None
        :rtype: None
        """
        await self.operations.run_relationship_event(self, source, 'unlink')

    @lifecycle_event_handler
    async def create(self):
        """
        Standard lifecycle coroutine to run create event

        :return: None
        :rtype: None
        """
        for target in self.context.deployment_plan[self]:
            if target.name != self.name:
                await target.link(self)

        await self.operations.run_standard_event(self, 'create')
        self.is_provisioned = True

    @lifecycle_event_handler
    async def configure(self):
        """
        Standard lifecycle coroutine to run ccnfigure event

        :return: None
        :rtype: None
        """
        await self.operations.run_standard_event(self, 'configure')

    @lifecycle_event_handler
    async def start(self):
        """
        Standard lifecycle coroutine to run start event

        :return: None
        :rtype: None
        """
        await self.operations.run_standard_event(self, 'start')

    @lifecycle_event_handler
    async def stop(self):
        """
        Standard lifecycle coroutine to run stop event

        :return: None
        :rtype: None
        """
        await self.operations.run_standard_event(self, 'stop')

    @lifecycle_event_handler
    async def delete(self):
        """
        Standard lifecycle coroutine to delete create event

        :return: None
        :rtype: None
        """
        await self.operations.run_standard_event(self, 'delete')
        for target in self.context.deployment_plan[self]:
            if target.name != self.name:
                await target.unlink(self)
        self.is_provisioned = False

    def __repr__(self):
        return 'Node {0}'.format(self.name)

    def serialize(self):
        """
        Serializes node critical information for further consumption

        :return: serialized node
        :rtype: dict
        """
        return {
            '__name': self.name,
            'is_provisioned': self.__provisioned,
            '__properties': self.__properties,
            '__attributes': self.__attributes,
            'runtime_properties': self.runtime_properties,
        }

    def load(self, **kwargs):
        """
        Loads node from serialized object

        :param kwargs: node attributes
        :return: node
        :rtype: OrchestraNode
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self
