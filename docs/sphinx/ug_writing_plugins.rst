---------------
Writing Plugins
---------------

.. warning::

    The plugin API is still preliminary: expect changes!

Additional activity and macro types can be added to *stressor* by the way of
*plugins*.

For example let's assume we need a new activity `PsAlloc` that is used like so:

.. code-block:: yaml

    - activity: PsAlloc
      allocate_mb: 1024
      per_session: true


This can be implemented by a separate installable Python module, that
exposes a special entry point:

.. code-block:: ini

    [options.entry_points]
    # Plugins are found by the 'stressor.plugins' namespace.
    # The 'register()' function is then called by the plugin loader.
    # The 'ps' name is used as stressor entry point name name.
    # The actual name of activities and macros is defined by the implementing
    # classes.
    stressor.plugins =
        ps = stressor_ps:register

See the `sample implementation <https://github.com/mar10/stressor-ps>`_
for implemntation details.

The new plugin will become available by installing it::

    $ pip install stressor-ps


.. note::

    Please let's reserve the namespace ``stressor-TASKNAME`` for 'official'
    extensions. |br|
    If you publish your own custom extension on PyPI, choose a name like
    ``stressor-USER-TASKNAME`` or similar.

    Also add 'stressor-plugin' to the keywords, to make it more discoverable.
