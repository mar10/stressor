----------------
Script Reference
----------------

..
    .. toctree::
    :hidden:


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
mock_result:
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
    Check if the headers match a regular expression, for example::

        assert_match_headers: ".*'DAV'.*"

    Note: Prepend ``(?i)`` to the expression to enable case insensitive match:
    ``"(?i).*'DAV'.*"``
assert_status
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
