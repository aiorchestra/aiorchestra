.. py:module:: aiorchestra.core.node

AIOrchestra Node API
====================

OrchestraNode class
-------------------

.. autoclass:: OrchestraNode

   ================================================= =
   API
   ================================================= =
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
   ================================================= =

   ================================== =
   Lifecycle events API
   ================================== =
    .. automethod:: create
    .. automethod:: configure
    .. automethod:: start
    .. automethod:: stop
    .. automethod:: delete
   ================================== =

   ================================== =
   Relationship events API
   ================================== =
    .. automethod:: create
    .. automethod:: configure
   ================================== =

