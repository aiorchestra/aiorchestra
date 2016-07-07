AIOrchestra Plugins API
=======================


Plugin
------

This two methods are designed to be used in plugins as base for implementing relationship and lifecycle events handlers.
So, in order to have robust and stable event execution each lifecycle coroutine should be wrapped with operations decorator.

Events implementation
---------------------

In order to get full power from async orchestration it is necessary to build events implementation in async way.
Using Python 3.5 capabilities it required to have implementation similar to examples below.

Standard lifecycle event

.. code-block:: python

    @utils.operation
    async def standard_event_method(node, *args):
        pass

Relationship event

.. code-block:: python

    @utils.operation
    async def relationship_event_method(source, target, inputs):
        pass


There's production ready `OpenStack plugin`_, by itself it might be a good example for writing your own plugins.


.. _OpenStack plugin: http://aiorchestra-openstack-plugin.readthedocs.io/en/latest/
