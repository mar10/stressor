Quickstart
----------

1. Install *stressor* ([details](installation))

2. Create a new scenario folder. For example:

    ```bash
    $ stressor init ./scenario_1
    ```

    or alternatively import an existing HAR file as a starting point
    ([details](ug_writing_scripts.html#importing-har-files)):

    ```bash
    $ stressor init ./scenario_1 --convert /path/to/output.har
    ```

3. Edit the scripts as needed (*users.yaml*, *main_sequence.yaml*, *scenario.yaml*)
  ([details](ug_writing_scripts))

4. Run the script:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml
    ```

    Use the `--monitor` argument to view the progress in a separate window:
    Also, `scenario.yaml` is the default, so we can omitt it and only pass the
    folder name:

    ```bash
    $ stressor run scenario_1 --monitor
    ```

    Use the `--log` argument to write output to a file or folder:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml --no-color --log .
    ```

    (Hit <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.)

<img src="_images/teaser.png">
