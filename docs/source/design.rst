AIOrchestra design
==================


TOSCA graph advanced processing
-------------------------------

Each TOSCA template represents a set of nodes and are somehow wired by use of
requirements and actual relationship implementation.
TOSCA template graph is a unordered graph where each node represents TOSCA
template node with its attributes like::

    requirements
    entity template
    relationships
    name
    type
etc.

But TOSCA graph is not really consumable as it is, because each node has collapsed requirements,
for example, node A  depends on nodes B, C, D, in its time node B has dependencies on C, E, etc.
So, as it can be seen, it is necessary to discover whole dependencies sequence without duplicates
and this dependency sequence should be ordered - in first place should appear node that has lowest
number of discovered dependencies, at the second place should appear node that has a dependency for first node, etc.
Basically, TOSCA graph does not appear to work like that, so it is not useful to create an executable from it.

This is why AIOrchestra processes TOSCA graph by discovering node dependencies and building sequenced ordered graph,
it has next view::

    node_a: [node_a,]
    node_b: [node_a, node_b]
    node_c: [node_a, node_b, node_c]

As it can be seen, each dependency sequence ends with key node itself, that's true, and if question will
be asked which node needs to be provisioned in order to accomplish its dependency sequence,
then the answer is - node itself as requirement to itself, "if i need to provision node A which
node should i provision before? Node A, of course."


AIOrchestra context
-------------------

AIOrchestra context represents TOSCA template and capabilities to transform it into executable
graph by providing set of API to manage deployment through its lifecycle

AIOrchestra node
----------------

AIOrchestra node represents a state of TOSCA node template with set of API to manage node through its lifecycle.
Node inherits TOSCA node template attributes like::

    properties
    attributes
    runtime_properties
    relationships
    requirements

Along with that each AIOrchestra node has node lifecycle events API::

    create
    start
    configure
    stop
    delete

Along with that each AIOrchestra node has relationship lifecycle events API::

    link
    unlink


Implementation details
----------------------

AIOrchestra works with `Python 3.5`_ or greater, therefore framework built on top of `asyncio`_ and related libraries.
In node/context API section more details will be discovered.


.. _Python 3.5: https://www.python.org/downloads/release/python-350/
.. _asyncio: https://docs.python.org/3/library/asyncio.html
