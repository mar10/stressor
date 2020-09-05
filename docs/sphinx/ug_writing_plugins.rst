---------------
Writing Plugins
---------------

.. warning::

    The plugin API is still preliminary: expect changes!

Additional activity and macro types can be added to *stressor* by the way of
*plugins*.

For example let's assume we need a new activity `memory` that is used like so:

.. code-block:: yaml

    - activity: memory
      allocate: 1GiB


This can be implemented by a separate installable Python module, that
exposes a special entry point:

.. code-block:: ini

    [options.entry_points]
    # Plugins are found by the 'stressor.plugins' namespace.
    # The 'register()' function is then called by the plugin loader.
    # The 'memory' name is used as stressor task type name.
    stressor.plugins =
        memory = stressor_memory:register

See the `sample implementation <https://github.com/mar10/stressor-memory>`_
for implemntation details and the
`sample project <https://github.com/mar10/test-stressor-memory/blob/master/stressor.yaml>`_
for a usage example.

The new plugin will become available by installing it::

    $ pip install stressor-memory


.. code-block:: py

    # TODO: Python implementation


.. seealso::
    In case you don't want to create a sub class of the passed in
    https://stackoverflow.com/a/9270908/19166

.. note::

    Please let's reserve the namespace ``stressor-TASKNAME`` for 'official'
    extensions. |br|
    If you publish your own custom extension on PyPI, choose a name like
    ``stressor-USER-TASKNAME`` or similar.

    Also add 'stressor-plugin' to the keywords, to make it more discoverable.
