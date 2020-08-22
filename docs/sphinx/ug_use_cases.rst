---------
Use Cases
---------

..
    .. toctree::
    :hidden:

Stressor may be used for several tasks.
Currently we focus on web applications.

Following a few recommendations, for a start.


Stress Tests
============

- Define a script that covers relevant functionality of your target application.
- Use ``duration: SECONDS`` and/or ``repeat: COUNT`` options for sequences,
  so we have a long-running test.
- Define ``sessions.users`` and ``sessions.count``, to simulate parallel user
  access.
- Optionally define ``monitor: true`` for selected activities, to collect extra
  statistics.
- Pass ``--monitor`` to view live progress in a separate browser window.


CI Tests
========

Run stressor as part of a continous integration workflow, e.g. inside Jenkins.

- Define a script that covers important functionality of your target application.
- Set the ``config.max_errors: 1`` option (or pass the``--max-errors=1`` argument),
  so the script will abort in case of errors as soon as possible.
- Set the ``config.max_errors=SECONDS`` option (or pass the ``--max-errors=SECONDS``
  argument), so unexpectedly long execution times will generate errors. |br|
  Of course the sequences should not be time constrained using the
  ``duration: SECONDS`` option for sequences in this case.
- Pass ``--log FOLDER`` so results can be reviewed later.
- Pass ``--verbose`` (``-v``) so logging will contain useful additional information.


Benchmarks
==========

- Pass ``--quiet`` (``-q``), so logging will not impact performance.
- Set the ``config.max_errors: 1`` option (or pass the``--max-errors=1`` argument),
  so we fail fast on errors (unless sporadic errors are tolerated).
- Define a script that runs for a given time, for example using the
  ``duration: SECONDS`` option for sequences. |br|
  Take note of 'activities per second per session' in the summary.
- Or define a script that runs a number of sequences, for example using the
  ``repeat: COUNT`` option for sequences. |br|
  Take note of 'run time' in the summary.
- Optionally define ``monitor: true`` for selected activities, to collect extra
  statistics.


Developing and Debugging Scripts
================================

- Pass ``--single`` so ``duration`` and ``repeat`` options are ignored.
- Pass ``--verbose`` (``-v``) or even ``-vv`` to print more information about
  requests and responses.
- Set the ``config.max_errors: 1`` option (or pass the ``--max-errors=1``
  argument), so we fail on the first error.
- Optionally define ``debug: true`` for selected activities, to print extra
  information.

See :doc:`ug_writing_scripts` for details.


Test Other Targets than Web-Applications
========================================

For example run a sequence of SQL statements against relational databases.

This is **not yet implemented**, but should become possible using the plugin
concept of a later version.
