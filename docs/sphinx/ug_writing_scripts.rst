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


Importing HAR Files
===================

`HAR files <https://en.wikipedia.org/wiki/HAR_(file_format)>`_ contain a list
of recorded browser requests. |br|
*stressor* can convert those files into its own format, e.g. a YAML formatted
sequence of HTTPRequest activities.

We can use the Chrome browser as macro recorder like so:

1. Open a Chrome tab and start the
   `developer tools <https://developers.google.com/web/tools/chrome-devtools>`_
   e.g. by hitting ``F12``.
2.  Activate the `Network` panel.
3. Clear the current network log if any.
4. Navigate to the URL that you want to record and perform your activities.
5. Select `Save all as HAR with content...`

Now convert the HAR file to a new *stressor* project::

    $ stressor init /path/to/scenario_name --convert /path/to/har_file.har

You probably want to edit ``scenario.yaml`` and ``main_sequence.yaml`` in
the ``/path/to/scenario_name/`` folder now.


Debugging
=========

Use the `--single` option to run all activities once, but only in one single
session. Also loop counts are ignored.

```bash
$ stressor run ./scenario_1/scenario.yaml --single
```
