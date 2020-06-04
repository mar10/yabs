======================
Command Line Interface
======================

.. toctree::
    :hidden:

Basic Command
=============

Use the ``--help`` or ``-h`` argument to get help::

    $ yabs --help
    usage: yabs [-h] [-v | -q] [-n] [--no-color] [-V]
                {run,bump,check,commit,exec,gh-release,push,pypi-release,tag} ...

    Release workflow automation tools.

    positional arguments:
    {run,bump,check,commit,exec,gh-release,push,pypi-release,tag}
                            sub-command help
        run                 run a workflow definition
        bump                increment current project version
        check               check preconditions
        commit              increment current 'patch' version (add `--minor` or
                            `--major`)
        exec                execute shell command
        gh-release          create a release on GitHub
        push                increment current 'patch' version (add `--minor` or
                            `--major`)
        pypi-release        Make sdist, wheel, and upload on PyPI
        tag                 increment current 'patch' version (add `--minor` or
                            `--major`)

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet           decrement verbosity by one
    -n, --dry-run         just simulate and log results, but don't change
                            anything
    --no-color            prevent use of ansi terminal color codes
    -V, --version         display version info and exit (combine with -v for
                            more information)

    See also https://github.com/mar10/yabs
    $


`run` command
-------------

The main purpose of the yabs command line tool is to execute a test
scenario::

    $ yabs run --inc patch

See also the help::

    usage: yabs run [-h] [-v | -q] [-n] [--no-color]
                    [--inc {major,minor,patch,postrelease}]
                    [workflow]

    positional arguments:
    workflow              run a workflow definition

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet           decrement verbosity by one
    -n, --dry-run         just simulate and log results, but don't change
                            anything
    --no-color            prevent use of ansi terminal color codes
    --inc {major,minor,patch,postrelease}
                            bump semantic version (used as default for `bump`
                            tasks)
    $


See the :doc:`user_guide` example for details.


Verbosity Level
---------------

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
----------

The CLI returns those exit codes::

    0: OK
    1: Error (network, internal, ...)
    2: CLI syntax error
    3: Aborted by user
