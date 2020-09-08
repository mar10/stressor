# ![logo](https://raw.githubusercontent.com/mar10/stressor/master/stressor/monitor/htdocs/stressor_48x48.png) stressor
[![Build Status](https://travis-ci.org/mar10/stressor.svg?branch=master)](https://travis-ci.org/mar10/stressor)
[![Latest Version](https://img.shields.io/pypi/v/stressor.svg)](https://pypi.python.org/pypi/stressor/)
[![License](https://img.shields.io/pypi/l/stressor.svg)](https://github.com/mar10/stressor/blob/master/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/stressor/badge/?version=latest)](http://stressor.readthedocs.io/)
[![Coverage Status](https://coveralls.io/repos/github/mar10/stressor/badge.svg?branch=master)](https://coveralls.io/github/mar10/stressor?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![StackOverflow: stressor](https://img.shields.io/badge/StackOverflow-stressor-blue.svg)](https://stackoverflow.com/questions/tagged/stressor)

> Stress-test your web app.

*Stressor* is a tool, that runs a sequence of activities in one or more
parallel sessions.
The most common use case is to run a test script with HTTP commands
against a web server, simulating a bunch of parallel user sessions.
As a result we get metrics about reponse times, failures, resource usage,
etc.

Stressor can be used for testing, benchmarking, load testing, or to generate
test data.
Stressor comes with prebuilt activities for HTTP-request and more, and can be
extended by custom activity-plugins.

Test scripts can be defined as text files, using a special syntax, that is then
executed by the `stressor` command line tool.
Stressor is also an Open Source Python library that can be included into your
own projects. This allows to define test *scenarios* programmtically.


## Quickstart

1. Install *stressor* ([details](https://stressor.readthedocs.io/en/latest/installation.html))

2. Create a new scenario folder. For example:

    ```bash
    $ stressor init ./scenario_1
    ```

    or alternatively import an existing HAR file as a starting point
    ([details](https://stressor.readthedocs.io/en/latest/ug_writing_scripts.html#importing-har-files)):

    ```bash
    $ stressor init ./scenario_1 --convert /path/to/output.har
    ```

3. Edit the scripts as needed (*users.yaml*, *main_sequence.yaml*, *scenario.yaml*)
  ([details](https://stressor.readthedocs.io/en/latest/ug_writing_scripts.html))

4. Run the script:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml
    ```

    Use the `--monitor` option to view the progress in a separate window:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml --monitor
    ```

    Use the `--log` argument to write output to a file or folder:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml --no-color --log .
    ```
    (Hit <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.)

5. [Read The Docs](https://stressor.readthedocs.io/en/latest/ug_tutorial.html)
   for details.

<img src="https://stressor.readthedocs.io/en/latest/_images/summary.png">

<img src="https://stressor.readthedocs.io/en/latest/_images/teaser.png">
