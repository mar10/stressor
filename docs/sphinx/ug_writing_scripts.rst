---------------
Writing Scripts
---------------

..
    .. toctree::
    :hidden:


Overview
========

Run configuration scripts are text files, that are read and compiled by the
*Context Manager*. This configuration is then passed to the *Run Manager*
for execution.

.. note::

    Unless you are a Python programmer, you may have to get used to the fact
    that **whitespace matters** in YAML files: |br|
    Make sure you indent uniformly. Don't mix tabs and spaces.
    We recommend to use an editor that supports the YAML syntax (e.g. VS Code).

A simple confuguration script may look like this: |br|
``scenario_1.yaml``:

.. literalinclude:: scenario_1.yaml
    :linenos:
    :language: yaml

The above example assumes the virtual users to be defined in a separate file,
for example: |br|
``users.yaml``:

.. literalinclude:: users.yaml
    :linenos:
    :language: yaml


Script Activities
-----------------

`RunScript` activities are the swiss army knife for the scenario definitions.
The follwing example shows inline script definitions.

.. code-block:: yaml
    :linenos:

    main:

    - activity: RunScript
        export: ["the_answer"]
        script: |
        the_answer = 6 * 7
        print("The answer is {}".format(the_answer))

    - activity: RunScript
        name: "GET example.com"
        # debug: true
        script: |
        r = session.browser.get("http://example.com")
        result = r.status_code




Debugging
=========

A **run configuration** describes all aspects of a test suite. It defines one
*scenario* and additional options.
