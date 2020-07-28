----------------
Script Reference
----------------

..
    .. toctree::
    :hidden:


Configuration
=============
General Configuration
---------------------

config.base_url
    Default: null
config.name
    Default: null
config.tag
    Default: null
config.details
    Default: null
config.verbose
    Default: null
config.timeout
    Default: null
config.max_errors
    Default: null
config.max_time
    Default: null

Session Configuration
---------------------

sessions.users
    The current user that is assigned to this session.
    ``users: $load(users.yaml)``
sessions.count
    ...
sessions.basic_auth
    Default: false
sessions.verify_ssl
    Default: true
sessions.ramp_up_delay
    Default: 0


Activities
==========
Common Args
-----------
All activites share these common arguments
(see also :class:`~stressor.plugins.base.ActivityBase`).

debug (bool, optional)
    Default: false
ignore_timing (bool, optional)
    Default: false, except for `Sleep` activities
monitor (bool, optional)
    Default: false
name (str, optional)
    ...
assert_match
    Check if the result matches a regular expression. |br|
    Tip: Prepend ``(?i)`` to the expression to enable case insensitive match::

        assert_match: "(?i).*foobar.*"


assert_max_time
    ...
if_session
    ...
if_session_not
    ...
mock_result:
    ...
store_json
    ...


HTTP Request Activities
-----------------------

The following arguments are passed directly to the
`requests <https://requests.readthedocs.io>`_ library:

auth (2-tuple, optional):
    ...
data (dict):
    Used to pass form-encoded data with POST requests.
json (dict):
    Used to pass JSON data with POST requests.
headers (dict):
    ...
params (dict):
    Pass URL arguments with GET/POST, ... requests.
timeout (float, optional):
    Request timneout in seconds (default: 10).
verify (bool, optional):
    False: ignore SSL certificate verification errors (default: True).

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


'RunScript' Activity
--------------------
(see also :class:`~stressor.plugins.script_activities.RunScriptActivity`).

export (bool|null|list, optional)
    List of local variable names (defined by the script) should be exported
    into the run context.
    Pass `null` or `false` to define 'no export wanted'.
    Omitting this argumet is considered 'undefined' and will emit a warning if
    the script defines variables.

path (str, optional)
    Path to a python file.

    .. code-block:: yaml

        - activity: RunScript
            export: ["the_answer"]
            path: "my_script.py"

script (str, optional)
    Python script code, e.g.

    .. code-block:: yaml

        - activity: RunScript
            export: ["the_answer"]
            script: |
            the_answer = 6 * 7
            print("The answer is {}".format(loclhost))

    Afterwars the context contains the result and can be accessed like
    ``$(the_answer)``.

'Sleep' Activity
----------------
:class:`~stressor.plugins.common.SleepActivity`

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

``$(context_var)``:
    This macro looks-up and returns a variable of the current run context,
    for examle ``$(base_url)``. Use dots ('.') to address sub-members, e.g.
    ``$(user.name)``.

``$sleep(duration)`` or ``$sleep(min, max)``:
    A shortcut to the ``Sleep`` activity (see above).

``$debug``:
    Dump the current run context (useful when debuggin scripts).
