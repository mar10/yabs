======================
Command Line Interface
======================

.. toctree::
    :hidden:

Basic Command
=============

Use the ``--help`` or ``-h`` argument to get help::

    $ yabs --help
    usage: yabs [-h] [-v | -q] [-n] [--no-color] [-V] {run} ...

    Release workflow automation tools.

    positional arguments:
    {run}          sub-command help
        run          run a workflow definition

    optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet    decrement verbosity by one
    -n, --dry-run  just simulate and log results, but don't change anything
    --no-color     prevent use of ansi terminal color codes
    -V, --version  display version info and exit (combine with -v for more information)

    See also https://github.com/mar10/yabs
    $


`run` command
=============

For example, publish a ne patch release::

    $ yabs run --inc patch

See also the help::

    $ yabs run --help
    usage: yabs run [-h] [-v | -q] [-n] [--no-color] [--force] [--no-release] [--no-progress]
                    [--inc {major,minor,patch,postrelease}] [--no-bump] [--force-pre-bump] [--no-check] [--gh-draft] [--gh-pre]    
                    [--no-winget-release]
                    [workflow]

    positional arguments:
    workflow              run a workflow definition

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet           decrement verbosity by one
    -n, --dry-run         just simulate and log results, but don't change anything
    --no-color            prevent use of ansi terminal color codes
    --force               allow to ignore some errors (like bumping above `max_increment`)
    --no-release          don't upload tags and assets to GitHub, PyPI, or winget-pkgs (but still build assets)
    --no-progress         do not display current progress table between tasks, even if verbose >= 3
    --inc {major,minor,patch,postrelease}
                            bump semantic version (used as default for `bump` task's `inc` option)
    --no-bump             run all 'bump' tasks in dry-run mode
    --force-pre-bump      bump `--inc postrelease` even if the current version is untagged
    --no-check            don't let the 'check' task stop the workflow (log warnings instead)
    --gh-draft            tell the github_release task to create a draft-release
    --gh-pre              tell the github_release task to create a pre-release
    --no-winget-release   run all 'winget_release' tasks in dry-run mode
    $


See the :doc:`user_guide` example for details.


Verbosity Level
===============

The verbosity level can have a value from 0 to 6:

=========  ======  ===========  =============================================
Verbosity  Option  Log level    Remarks
=========  ======  ===========  =============================================
  0        -qqq    CRITICAL     quiet
  1        -qq     ERROR
  2        -q      WARN         show less info
  3                INFO         show write operations
  4        -v      DEBUG        show more info
  5        -vv     DEBUG
  6        -vvv    DEBUG
=========  ======  ===========  =============================================


Exit Codes
==========

The CLI returns those exit codes::

    0: OK
    1: Error (network, internal, ...)
    2: CLI syntax error
    3: Aborted by user
