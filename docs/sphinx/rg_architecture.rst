============
Architecture
============

..
    .. toctree::
    :hidden:


Overview
========

|stressor| is a tool, that runs a sequence of activities in one or more
parallel sessions. |br|
The most common use case is to run a test script with HTTP commands
against a web server, simulating a bunch of parallel user sessions. |br|
As a result we get metrics about reponse times, failures, resource usage,
etc.


Concepts
========

The :class:`stressor.run_manager.RunManager` ...

  - Run manager
  - Session manager
  - Config manager


Class Overview
==============

Activities & Macros
-------------------

.. inheritance-diagram:: stressor.plugins.base stressor.plugins.common stressor.plugins.http_activities stressor.plugins.script_activities
   :parts: 2
   :private-bases:
   :caption: Standard Stressor Activities and Macros

Session Runner
--------------

.. inheritance-diagram:: stressor.run_manager stressor.context_stack stressor.session_manager stressor.config_manager stressor.statistic_manager
   :parts: 2
   :private-bases:
   :caption: Session Runner


.. |stressor| raw:: html

   <a href="https://en.wikipedia.org/wiki/Stressor"><abbr title="A stressor is a chemical or biological agent, environmental condition, external stimulus or an event that causes stress to an organism.">stressor</abbr></a>
