----------
Quickstart
----------

1. Install *stressor* ([details](installation.html))

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
  ([details](ug_writing_scripts.html))

4. Run the script:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml
    ```

    Use the `--monitor` argument to view the progress in a separate window:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml --monitor
    ```

    Use the `--log` argument to write output to a file:

    ```bash
    $ stressor run ./scenario_1/scenario.yaml --no-color --log c:\temp\stressor_latest.log
    ```

    (Hit <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.)

<img src="_images/teaser.png">
