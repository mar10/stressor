# stressor

> Stress-test your web app.


## Goals

  - A library
  - A CLI
  - Allow declarative definition of test sequences
  - Extendable by Python plugins
  - Not only Web-Requests, but general *acvtivities*, e.g. SQL request


## Overview



## Modules

  - CLI
  - SessionManager

## System tokens

`$` this prefix is used in the declarative syntax to denote a system token.

The `$` namespace refers to current execution **context**.
For example `$.root` may contain the root URL of the target application.
These variables may be set by the configuration scripts and dynamically by the
actions during execution.

System varaibles

  - `$.root`: URL
  - `$.session`:
  - `$.user`:

System methods used in Scripts:

  - `$pick(<list>)`
  - `$next(<list>)`
  - `$exec(<script_name>)`
  - `$import(<file_name>)`
  - `$append_array(<file_name>)`
  - `$fabulate(<template>)`

Activities:

  - P


## Example Project Definition

`my_project_1.yaml`:

```yaml
# Stressor Project Definition
# See https://github.com/mar10/stressor
# The project name is derived from the filename without `.yaml` extension.

# System Settings.
# This values override the system default, but can be overriden by command line args or run configuration
config:
  verbose: 3
  logging:
    target: ./results

# Context Parameters used by Activities.
# All used parameters must be listed here in the form:
#   parameter_name: default_value
# Set `null` value to make it mandatory, i.e. must be passed by caller.
params:
  base_url: null
  user_count: 1
  timeout_fail: 300
  timeout_warn: 0.5
  sleep_between_pages: 5
  max_pages_per_session: 100
  max_secs_per_session: -1

# Steps are short sequences of activities and/or steps.
# This section defines some global steps that may be used in suites or other step definitions.
steps:
  # Activities are defined as a list of dicts.
  # The key `activity` matches the class name of a system or custom activity.
  # All other keys are passed to the activity as named args.
  # Since the current context is passed to the activity (in addition to the listed named keys),  activities know about `user`, `base_url`, etc.

  # A step named 'log_in_directly'.
  log_in_directly:
    - activity: BasicAuthLoginActivity
      url: $(base_url)/my-login-service

  log_in_with_form:
    - activity: PostRequestActivity
      url: $(base_url)/my-login-service
      data:
        - name: $(user).name
        - password: $(user).password

  log_out:
    - activity: GetRequestActivity
      url: $(base_url)/my-logout

# Suites are sequences of Steps and/or Activities.
# These steps can be
suites:
  # Test-suite 'load_pages'
  load_pages:
    # Suite parameters override the parent context
    params:
      a: 1

    # Sessions define the number of parallel tests.
    # The `steps` sequence is executed once per user.
    sessions:
      users: $(user_list)
      max_parallel: $(parallel_session_count)
      max_count: $(session_count)
      session_runtime: $(max_secs_per_session)


    # Steps are defined as a list of either
    #   - string name of an existing step
    #   - dict with a `step` key
    #   - dict with a `activity` key
    #   - dict with a `loop` key
    steps:
      - log_in_with_form
      - loop:
          until_count: $(max_pages_per_session)
          until_elap: $(max_secs_per_session)
          steps:
            # Load a random URL from the list
            - activity: GetRequestActivity
              url: $(pick_any:page_url_list)
              checks:
                contains: "ERROR"
                matches: "/sOk/s"
            - activity: SleepActivity
              seconds: $(sleep_between_pages)
      - log_out

#

```

## Example Run Configuration

A run configuration file defines and overrides parameters of the project definition

`my_run_config.yaml`:

```yaml
tag: Test-Run STAGING nightly $(datetime_iso)
project: ./my_project_1
params:
  base_url: https://example.com/staging_server/my_app
suites:
  - load_page
```

General Hierarchical Structure

```
Project definition
    Suite definition List (== SEQUENCE, SCENARIO)
        Step List (Steps may have sub-Steps)
            Action List

RunParameters
```

A `Run` is the execution of one `Suite` with a set of Parameters.
```bash
$ stressor run
```

```
Project
    Suite
        Step
            Action | Step

RunParameters
```

# Dec
