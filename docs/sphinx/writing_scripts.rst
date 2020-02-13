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


Session Configuration
=====================

users
    The current user that is assigned to this session.
    ``users: $load(users.yaml)``
count:
    ...
base_url
    Default: null
basic_auth
    Default: false
verify_ssl
    Default: true


Activities
==========


Common Args
-----------
All activites share these common arguments
(see also :class:`stressor.base.ActivityBase`).

debug
    ...
monitor
    ...
assert_match
    ...
assert_max_time
    ...
store_json
    ...
if_session
    ...
if_session_not
    ...


HTTP Request Activities
-----------------------

Passed directly to the `requests` library:

auth:
    ...
data:
    ...
json:
    ...
headers
    ...
params
    ...
timeout
    ...
verify
    ...

Additional arguments:

assert_html
    ...
assert_json
    ...
assert_match_headers
    ...
assert_status
    ...
mock_result:
    ...


Script Activities
-----------------
(see also :class:`stressor.script_activities.RunScriptActivity`).

export
    ...
path
    ...
script
    ...

Sleep Activities
----------------
:class:`stressor.common.SleepActivity`

duration
    ...
duration_2
    ...


Context Variables
=================

user
    The current user that is assigned to this session.

base_url
    Default: null


Macros
======

$(`context_var`)
    ...

$sleep(min, max)
    ...

$debug
    ...


Debugging
=========

A **run configuration** describes all aspects of a test suite. It defines one
*scenario* and additional options.
