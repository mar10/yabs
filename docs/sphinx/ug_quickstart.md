Quickstart
----------

1. Install *yabs* ([details](installation))

2. Create and edit the workflow definition script (*yabs.yaml*)
  ([details](ug_writing_scripts))

3. Run the script:

    ```bash
    $ yabs run --inc patch
    ```

    Use the `--dry-run` or `-n` argument test the workflow without really releasing.<br>
    Use the `--workflow` argument to specify the location of the coniguration file if it is not the default `./yabs.yaml` verbosity.

    ```bash
    $ yabs run --inc minor --workflow /path/to/yabs.yaml --dry-run
    ```

<img src="_images/teaser.png">
