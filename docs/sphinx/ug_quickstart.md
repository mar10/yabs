# Quickstart

1. Install *yabs* ([details](installation))

2. Create a definition script (*yabs.yaml*) inside your project directory
   ```bash
   $ yabs init
   ```
   and edit it to your needs ([details](ug_writing_scripts)).

3. Check the current project status
   ```bash
   $ yabs info
   ```
    Add the `--check` or `-c` argument to also test the release preconditions.

4. Run the script to make a new release:

    ```bash
    $ yabs run --inc patch
    ```

    Specify the `--inc` bump type (*patch*, *minor*, *major*, *postrelease*).<br>
    Use the `--dry-run` or `-n` argument to test the workflow without really releasing.<br>
    Use the `--verbose` or `-v` to increase verbosity. <br>
    Use the `--workflow` argument to specify the location of the configuration
    file if it is not at the default location *./yabs.yaml*.

    ```bash
    $ yabs run --inc minor --workflow /path/to/yabs.yaml --dry-run
    ```

<img src="_images/screenshot_ps_dryrun.png">
