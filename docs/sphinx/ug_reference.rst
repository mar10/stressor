----------------
Script Reference
----------------

..
    .. toctree::
    :hidden:


Configuration
=============

The whole *stressor* confiuration is stored in a single YAML file with a few
attributes and 5 mandatory sections.

See :doc:`ug_sample_stressor_yaml` for an example.

Top-level Attributes
--------------------

file_version (str)
    File identifier, must be ``file_version: 'stressor#0'``.


'config': Section
-----------------

This section contains general configuration.

config.base_url (str, default: `''`)
    Prefix that is prepended to relative URLs in HTTP activities.
    Example: ``base_url: 'http://example.com/foo'``
config.name (str, default: `file name`)
    Scenario name (defaults to name of this file without '.yaml' extension)
config.tag (int, default: `''`)
    Optional string that describes the current run.
    May be used to display additional info about boundary conditions, etc.
    Example 'Test-Run STAGING nightly'
    (pass `-o "tag:MY TAG INFO"` to override)
config.details (int, default: `''`)
    Optional multi-line string with additional info.
config.verbose (int, default: `3`)
    Output verbosity level [0..5]. (See also ``--verbose``/``-v`` argument)
config.request_timeout (float, default: `null`)
    Default timeout in seconds for web requests (i.e. HTTP activities)
    This value can be overridden with HTTP-Activity's `timeout` parameter
config.max_errors (int, default: `0`)
    Maximum total error count that is tolerated before stopping.
    Override with `--max-errors` argument.
    Default 0 means: don't stop on errors.
config.max_time (int, default: `0.0`)
    (float) Max. run time in seconds before stopping (override with `--max-time`)
    Default 0.0 means: no time limit.


'context' Section
-----------------

When a scenario is run, one separate *context* dictionary is created per session.
This instance is then passed to every activity of the session's sequences, so
activities can read and write from/to it.

The context dictionary inherits all entries from the 'config' section above,
but we can optionally add new or override exising settings here.


'sessions' Section
------------------

This run configuration defines how the `sequences` are executed in parallel
sessions.

sessions.users (list, default: `[]`)
    Defines a list of user dicts, with at least `name` and `pasword`
    attributes. Often stored in a separate file and included like so:
    ``users: $load(users.yaml)``
sessions.count (int, default: `1`)
    Number of sessions (virtual users). If greater than no. of users,
    users will be re-used round robin.
sessions.duration (float, default: `0.0`)
    max. run time in seconds, before the session stops. The current
    and the 'end' sequences are completed.
    Default: 0.0 means no time limit.
sessions.basic_auth (bool, default: `false`)
    Pass true to enable HTTP basic authentication, using user's credentials.
sessions.verify_ssl (bool, default: `true`)
    Pass false to ignore SSL certificate errors.
sessions.ramp_up_delay (float, default: `0.0`)
    Waiting time between starting distinct user sessions in seconds.
    Default 0.0 means start all session at once.


'scenario' Section
------------------

Define the order and duration of sequences that every virtual user session
performs.
All sequence definitions that are referenced here, must also appear in the
following `sequences` section.

.. code-block:: yaml

    scenario:
      - sequence: init  # This is typically the first sequence
      - sequence: SEQUENCE_NAME
      - sequence: SEQUENCE_NAME
      - sequence: end  # This is typically the last sequence

scenario_item.sequence (str)
    'init' is the reserved name for the set-up sequence, like logging-in.
    If errors occur here, all subsequent sequences (including 'end') are skipped.

    Other sections can have arbitrary names and are excuted in order of
    appearance.
    Sequence names may occur multiple times.

    'end' is the reserved name for the tear-down sequence (e..g. log out).
    This sequence is executed even if errors in previous sequences caused the
    scenario to stop.

scenario_item.duration (float, default: `0.0`)
    This sequence is repeated in a loop, until `duration` seconds are reached
    (always completing the current sequence).
    Default: 0.0 means no time-based looping.

scenario_item.repeat (int, default: `0`)
        This sequence is repeated in a loop, until `duration` seconds are
        reached (always completing the full sequence).
        Default: 0 (or 1) means no repeat.


'sequences' Section
-------------------
List of named action sequences. Used as building blocks for scenarios:

.. code-block:: yaml

    sequences:
      SEQUENCE_NAME_1:
        - activity: ACTIVITY_NAME
          ...  # activity arguments
        - activity: ACTIVITY_NAME
          ...
      SEQUENCE_NAME_2:
        - activity: ACTIVITY_NAME
          ...
        - activity: ACTIVITY_NAME
          ...

See below for details on activites.


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
