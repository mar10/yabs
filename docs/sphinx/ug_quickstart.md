Quickstart
----------

1. Install *yabs* ([details](installation))

2. Create a new scenario folder. For example:

    ```bash
    $ yabs init ./scenario_1
    ```

    or alternatively import an existing HAR file as a starting point
    ([details](ug_writing_scripts.html#importing-har-files)):

    ```bash
    $ yabs init ./scenario_1 --convert /path/to/output.har
    ```

3. Edit the scripts as needed (*users.yaml*, *main_sequence.yaml*, *scenario.yaml*)
  ([details](ug_writing_scripts))

4. Run the script:

    ```bash
    $ yabs run ./scenario_1/scenario.yaml
    ```

    Use the `--monitor` argument to view the progress in a separate window:

    ```bash
    $ yabs run ./scenario_1/scenario.yaml --monitor
    ```

    Use the `--log` argument to write output to a file or folder:

    ```bash
    $ yabs run ./scenario_1/scenario.yaml --no-color --log .
    ```

    (Hit <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop.)

<img src="_images/teaser.png">
