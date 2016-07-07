.. py:module:: aiorchestra.core.context

AIOrchestra Context API
=======================

OrchestraContext
----------------

.. autoclass:: OrchestraContext


   ================================== =
   Context properties
   ================================== =
    .. automethod:: outputs
    .. automethod:: status
    .. automethod:: nodes
    .. automethod:: name

   ================================== =
   API
   ================================== =
    .. automethod:: node_from_name
    .. automethod:: deployment_plan
    .. automethod:: deploy
    .. automethod:: undeploy
    .. automethod:: run_deploy
    .. automethod:: run_undeploy
    .. automethod:: serialize
    .. automethod:: load

