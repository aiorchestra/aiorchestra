.. py:module:: aiorchestra.core.node

AIOrchestra Node API
====================

OrchestraNode class
-------------------

.. autoclass:: OrchestraNode


   ================================== =
   Node properties
   ================================== =
    .. automethod:: custom_defs
    .. automethod:: node_type_definition
    .. automethod:: node_type
    .. automethod:: type_definition
    .. automethod:: property_definishion
    .. automethod:: capabilities
    .. automethod:: artifacts
    .. automethod:: name
    .. automethod:: is_provisioned
    .. automethod:: properties
    .. automethod:: attributes
    .. automethod:: runtime_properties
    .. automethod:: has_parents
    .. automethod:: parent_nodes
    .. automethod:: has_children
    .. automethod:: child_nodes

   ================================== =
   API
   ================================== =
    .. automethod:: get_capability
    .. automethod:: get_artifact_from_type
    .. automethod:: get_artifact_by_name
    .. automethod:: process_output
    .. automethod:: attempt_to_validate
    .. automethod:: update_runtime_properties
    .. automethod:: batch_update_runtime_properties
    .. automethod:: get_attribute
    .. automethod:: get_requirement_capability
    .. automethod:: serialize
    .. automethod:: load

   ================================== =
   Lifecycle events API
   ================================== =
    .. automethod:: create
    .. automethod:: configure
    .. automethod:: start
    .. automethod:: stop
    .. automethod:: delete

   ================================== =
   Relationship events API
   ================================== =
    .. automethod:: create
    .. automethod:: configure
