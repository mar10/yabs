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
    Use the `--verbose` or `-v` to increase verbosity. <br>
    Use the `--workflow` argument to specify the location of the configuration
    file if it is not at the default location *./yabs.yaml*.

    ```bash
    $ yabs run --inc minor --workflow /path/to/yabs.yaml --dry-run
    ```

<img src="_images/teaser.png">
