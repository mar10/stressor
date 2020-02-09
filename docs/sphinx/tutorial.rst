--------
Tutorial
--------

..
    .. toctree::
    :hidden:


Overview
========

|stressor| is a tool, that runs a sequence of activities in one or more
parallel sessions. |br|
The most common use case is to run a test script with HTTP commands
against a web server, simulating a bunch of parallel user sessions. |br|
As a result we get metrics about reponse times, failures, resource usage,
etc.

Stressor can be used for testing, benchmarking, load testing, or to generate
test data. |br|
Stressor comes with prebuilt activities for HTTP-request and more, and can be
extended by custom activity-plugins.

Test scripts can be defined as text files, using a special syntax, that is then
executed by the `stressor` command line tool. |br|
Stressor is also an Open Source Python library that can be included into your
own projects. This allows to define test *scenarios* programmtically.


Concepts
========

A **run configuration** describes all aspects of a test suite. It defines one
*scenario* and additional options.

A **scenario** defines a list of *sequences* that are executed in order,
possibly looping. Think of it as a kind of story book that describes one user's
behavior. |br|
During a run, the scenario is executed in one or more parallel user *sessions*.

**Sequences** are lists of *activities* that are executed in order.
Sequences named 'init' and 'end' are typically reserved to set-up and tear-down
scenarios. Often we have a looping 'main' sequence in the middle, but we
can define more sequences with arbitrary names.

**Activities** are the smallest building blocks of scenarios.
Typical activies are `GetRequest`, `PutRequest`, `RunScript`, `Sleep`, ... |br|
Every activity can be configured, for example with a request URL and
parameters, checks for expected results, etc. |br|
Custom **plugins** can be developed and installed to make additional activities
available.

While the *scenario* is executed, a dictionary of global variables is
available. Activities can access this **context** in order to read
configuration or pass information along.

**Macros** are used in activity definitions to pass *context* variables as
options.

When a scenario is run, one or more  **sessions** are executed in parallel.
Every session has a virtual *user* assigned.

The **command line interface** (CLI) can be run from the computer console. It
will read and compile the configuration file, execute the scenario, and display
results and statistics. |br|
Alternativly include the **Python `stressor` package** in your project, define,
configure, and run the scenario programmatically.

The *CLI* can open a **monitor** application that displays the current
execution statistics in real time.


Architecture
============

  - Run manager
  - Session manager
  - Config manager


..
    .. note::

        The CLI calls ``set_pyftpsync_logger(None)`` on startup, so it logs to stdout
        (and stderr).


.. |stressor| raw:: html

   <a href="https://en.wikipedia.org/wiki/Stressor"><abbr title="A stressor is a chemical or biological agent, environmental condition, external stimulus or an event that causes stress to an organism.">stressor</abbr></a>
