Reference Guide
===============

Class Overview
--------------

Activities & Macros
~~~~~~~~~~~~~~~~~~~

.. inheritance-diagram:: stressor.plugins.base stressor.plugins.common stressor.plugins.http_activities stressor.plugins.script_activities
   :parts: 2
   :private-bases:
   :caption: Standard Stressor Activities and Macros

Session Runner
~~~~~~~~~~~~~~

.. inheritance-diagram:: stressor.run_manager stressor.context_stack stressor.session_manager stressor.config_manager stressor.statistic_manager
   :parts: 2
   :private-bases:
   :caption: Session Runner


Algorithm
---------

TODO


API Reference
-------------

.. toctree::
   :maxdepth: 4

   modules
   genindex


.. genindex fails when an epub is created with Sphinx 1.5
   Sphinx 1.6 is not yet supported by RTD
   genindex
