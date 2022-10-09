----------------
Script Reference
----------------

..
    .. toctree::
    :hidden:


Configuration
=============

The whole *stressor* confiuration is stored in a single YAML file with a few
attributes and five mandatory sections.

.. seealso::
    See the annotated :doc:`ug_sample_stressor_yaml` for an example.

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
config.details (str, default: `''`)
    Optional multi-line string with additional info.
config.max_errors (int, default: `0`)
    Maximum total error count that is tolerated before stopping.
    Override with `--max-errors` argument.
    Default 0 means: don't stop on errors.
config.max_time (float, default: `0.0`)
    (float) Max. run time in seconds before stopping (override with `--max-time`)
    Default 0.0 means: no time limit.
config.name (str, default: `file name`)
    Scenario name (defaults to name of this file without '.yaml' extension)
config.request_timeout (float, default: `null`)
    Default timeout in seconds for web requests (i.e. HTTP activities)
    This value can be overridden with HTTP-Activity's `timeout` parameter
config.tag (str, default: `''`)
    Optional string that describes the current run.
    May be used to display additional info about boundary conditions, etc.
    Example 'Test-Run STAGING nightly'
    (pass `-o "tag:MY TAG INFO"` to override)
config.verbose (int, default: `3`)
    Output verbosity level [0..5]. (See also ``--verbose``/``-v`` argument)


'context' Section
-----------------

When a scenario is run, one separate *context* dictionary is created per session.
This instance is then passed to every activity of the session's sequences, so
activities can read and write from/to it using macro syntax: |br|
``$(context_name)``

The context dictionary inherits all entries from the 'config' section above,
but we can optionally add new or override exising settings here. |br|
Values may also be defined or overridden using the the command line, e.g.
`--option "NAME:VALUE"`

.. seealso::
    See also the `Context Variables`_ section below for details.


'sessions' Section
------------------

This run configuration defines how the `sequences` are executed in parallel
sessions.

sessions.basic_auth (bool, default: `false`)
    Pass true to enable HTTP basic authentication, using user's credentials.
sessions.count (int, default: `1`)
    Number of sessions (virtual users). If greater than no. of users,
    users will be re-used round robin.
sessions.max_duration (float, default: `0.0`)
    Maximum run time in seconds, before the session stops. The current
    and the 'end' sequences are completed.
    Default: 0.0 means no time limit.
sessions.min_duration (float, default: `0.0`)
    Minimal run time in seconds, before the session stops. The main
    sequences (all sequences excluding 'init' and 'end') are repeated in a loop
    until this time is reached. After that, the 'end' sequence is run.
    Default: 0.0 means no time looping.
sessions.ramp_up_delay (float, default: `0.0`)
    Waiting time between starting distinct user sessions in seconds.
    Default 0.0 means start all session at once.
sessions.repeat (int, default: `0`)
    The main sequences (all sequences excluding 'init' and 'end') are
    repeated in a loop N times. After that, the 'end' sequence is run.
    Default: 0 (or 1) means no looping.
sessions.users (list, default: `[]`)
    Defines a list of user dicts, with at least `name` and `pasword`
    attributes. Often stored in a separate file and included like so:
    ``users: $load(users.yaml)`` |br|
    If no users are defined, one user is assumed:
    ``{"name": "anonymous", "password": ""}``.
sessions.verify_ssl (bool, default: `true`)
    Pass false to ignore SSL certificate errors.


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
        repeat: 3  # optional
      - sequence: SEQUENCE_NAME
        duration: 30.0  # optional
      - sequence: end  # This is typically the last sequence

scenario_item.sequence (str)
    'init' is the reserved name for the set-up sequence, like logging-in.
    If errors occur here, all subsequent sequences (including 'end') are skipped.

    Other sections can have arbitrary names and are excuted in order of
    appearance. |br|
    Sequence names may occur multiple times.

    'end' is the reserved name for the tear-down sequence (e.g. log out or
    cleanup fixtures). |br|
    This sequence is executed even if errors in previous sequences caused the
    scenario to stop.

scenario_item.duration (float, default: `0.0`)
    This sequence is repeated in a loop, until `duration` seconds are reached
    (always completing the current sequence).
    Default: 0.0 means no time-based looping.

scenario_item.repeat (int, default: `1`)
        This sequence is repeated in a loop, until `repeat` iterations are
        completed.


'sequences' Section
-------------------
List of named action sequences. Used as building blocks for scenarios:

.. code-block:: yaml

    sequences:
      SEQUENCE_NAME_1:
        - activity: ACTIVITY_TYPE
          ...  # activity arguments
        - activity: ACTIVITY_TYPE
          ...
      SEQUENCE_NAME_2:
        - activity: ACTIVITY_TYPE
          ...
        - activity: ACTIVITY_TYPE
          ...

See below for details on `Activities`_.


Activities
==========

Activities are defined as part of a sequence list like so:

.. code-block:: yaml

    - activity: ACTIVITY_TYPE
    ...

.. seealso::
    See also some examples: :doc:`ug_sample_stressor_yaml` and
    :doc:`ug_writing_scripts`.

Common Args
-----------
All activites share these common arguments
(see also :class:`~stressor.plugins.base.ActivityBase`).

activity (str)
    The activity type, e.g. "GetRequest", "RunScript", or "Sleep". |br|
    Also macros like "$sleep(0.3)" are accepted.
assert_match (str, optional)
    Check if the result matches a regular expression. |br|
    Tip: Prepend ``(?i)`` to the expression to enable case insensitive match::

        assert_match: "(?i).*foobar.*"

assert_max_time (float, optional)
    Trigger error if execution takes longer than `x` seconds.
debug (bool, default: `false`)
    Increase logging for this activity.
ignore_timing (bool, default: `false`)
    If true, this activity's run time does not count towards the 'net time'
    statistics. |br|
    For `Sleep` activities this defaults to true.
mock_result (any, optional):
    If dry-run mode is active, this activity is not run, but instead the value
    of `mock_result` is stored as `context.last_result`.
monitor (bool, default: `false`)
    Pass true to collect and display statistics for this activity as a separate
    line.
name (str, default: `''`)
    A name that will be used when logging this activity.
store_json (str, optional)
    Store a part of the activity's JSON result as `context` variable. |br|
    For example if the activity returns
    ``{"response": {"key": "1234abc"}}`` for this request::

        - activity: GetRequest
          url: /my_target
          store_json:
            res_key: 'response.key'

    We would create a context variable that would be accessible as
    ``$(res_key)`` == "1234abc".
    (See also the ``assert_json`` argument of HTTP activities.)

.. if_session
..     ...
.. if_session_not
..     ...


HTTP Request Activities
-----------------------

Stressor defines a generic
:class:`~stressor.plugins.http_activities.HTTPRequestActivity` class, that
accepts (among others) a ``method`` argument. |br|
These four convenience activities are direct derivatives that set the ``method``
argument accordingly: |br|
:class:`~stressor.plugins.http_activities.GetRequestActivity`,
:class:`~stressor.plugins.http_activities.PostRequestActivity`,
:class:`~stressor.plugins.http_activities.PutRequestActivity`,
:class:`~stressor.plugins.http_activities.DeleteRequestActivity`.

(Another related activity is the
:class:`~stressor.plugins.http_activities.StaticRequestsActivity`.)

Following a list of activity arguments. |br|
**Note:** Arguments marked with *[req]* are passed directly to the
`requests <https://requests.readthedocs.io>`_ library.


assert_html (dict, optional)
    Check if the response has HTML format and matches an XPath expression::

        - activity: GetRequest
        url: /
        assert_html:
            "//*[@class='logo']": true

    (See also the common ``assert_match`` argument.)

assert_json (dict, optional)
    Check if the response has JSON format and contains a specific value
    or format, e.g.
    ``{"status": "ok", "result": {"guid": "{BBFC98E6-DD92-473C-A65C-BDD868E64CF2}"}}``::

        - activity: GetRequest
          url: /my_target
          assert_json:
            status: 'ok'
            result.guid: '[{]?[0-9a-fA-F\-]{36}[}]?'

    (See also the common ``store_json`` argument.)

assert_match_headers (str, optional)
    Check if the headers match a regular expression, for example::

        assert_match_headers: ".*'DAV'.*"

    Prepend ``(?i)`` to the expression to enable case insensitive match:
    ``"(?i).*'DAV'.*"``

assert_status (list[int], optional)
    Normally HTTP requests raise an error if the return status code is 4xx, 5xx,
    etc. |br|
    Here we can define a list of status codes that will be considerd 'success'.
auth (2-tuple, optional) *[req]*
    ``(username, password)`` will be used for HTTP Basic Authentication. |br|
    The default for this setting is defined by the ``config.basic_auth``
    option: if true, this tuple will be defined as ``(user.name, user.password)``
    for the current session.
data (dict, optional) *[req]*
    Used to pass form-encoded data with POST requests.
json (dict, optional) *[req]*
    Used to pass JSON data with POST requests.
headers (dict, optional) *[req]*
    Pass additional headers with the request.
method (str)
    This is mandatory for the
    :class:`~stressor.plugins.http_activities.HTTPRequestActivity`:
    passing "GET" is equivalent to using
    :class:`~stressor.plugins.http_activities.GetRequestActivity` for example. |br|
    Other common values could "OPTION", "HEAD", ...
params (dict, optional) *[req]*
    Pass URL arguments with GET/POST, ... requests.
timeout (float, optional) *[req]*
    Request timeout in seconds (default: infinite). |br|
    Note: the default for this flag is defined by the ``config.request_timeout``
    option.
url (str) *[req]*
    Target URL for the request. |br|
    For relative URLs (no server part), the ``config.base_url`` prefix will be
    added: |br|
    ``url: /my_target`` is equivalent to ``url: $(base_url)/my_target``.
verify (bool, optional) *[req]*
    False: ignore SSL certificate verification errors. |br|
    The default for this flag is defined by the ``config.verify_ssl``
    option.


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

    Afterwards the context contains the result and can be accessed like
    ``$(the_answer)``.


'Sleep' Activity
----------------
:class:`~stressor.plugins.common.SleepActivity`

duration (float)
    Sleep time in seconds.
duration_2 (float, optional)
    If defined, the sleep time will be a random value in the range
    [duration .. duration_2].


Context Variables
=================

When a scenario is run, one separate *context* dictionary is created per
session. |br|
The *context*  contains all entries from the 'config' section and everything
that was added to the 'context' section. |br|
Values may also be defined or overridden via the command line, e.g.
``--option "NAME:VALUE"``.

This instance is then passed to every activity of the session's sequences, so
activities can read it using macro syntax, e.g ``$(var_name)``. |br|
Activitites may als write to the context, for example by using the ``store_json``
or ``export`` argument.

Finally, also these values are added:

dry_run (bool)
    If true, activities should avoid to perform write operations.
last_result (any)
    The result of the previous activity. Mostly a string, possibly truncated
    to a reasonable length.
session_id (str)
    The ID of the current session, e.g. ``"t03"``. |br|
    This string may be handy to construct session-specific file names, URLs, etc.::

        - activity: PutRequest
          url: /wsgidav_test_file~$(session_id).txt

user (dict)
    The current user that is assigned to this session. |br|
    'name' and password are always present, but we can also add custom
    attributes to the user list entries. |br|
    Access properties like ``$(user.name)``, ``$(user.password)``,
    ``$(user.field_1)``, ...
verbose (int)
    0: quiet .. 5: maximal verbose

See `Macros`_ below for details on how to access those attributes in action
definitions.


Macros
======

``$(context_var)``:
    This macro looks-up and returns a variable of the current run context,
    for examle ``$(base_url)``, ``$(session_id)``.  |br|
    Use dots ('.') to address sub-members, e.g. ``$(user.name)``.

``$sleep(duration)`` or ``$sleep(min, max)``:
    A shortcut to the ``Sleep`` activity (see above).

``$debug``:
    Dump the current run context (useful when debugging scripts).
