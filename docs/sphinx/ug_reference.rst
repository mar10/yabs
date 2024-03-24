----------------
Script Reference
----------------

Workflow Configuration
======================

At the beginning of the configuration file, we define general options
for all following tasks in this workflow:

.. code-block:: yaml

    file_version: yabs#1

    config:
      repo: 'mar10/test-release-tool'
      gh_auth:
        oauth_token_var: GITHUB_OAUTH_TOKEN
      version:
        - type: __version__
          file: src/test_release_tool/__init__.py
      max_increment: minor
      branches:  # Current branch must be in this list
        - main  # Used by GitHub since 2020-11
        - master  # legacy 

branches (str | list), default: *null*
    Git branch name (or list of such) that are allowed. |br|
    This check is typically used to prevent creating accidental releases from
    feature or maintenance branches.

gh_auth (dict | str), *mandatory*
    Name of the environment variable that contains your
    `GitHub OAuth token <https://docs.github.com/en/github/extending-github/git-automation-with-oauth-tokens>`_ :

    oauth_token_var (str)
        oauth_token_var: GITHUB_OAUTH_TOKEN

max_increment (str)
    Restrict the maximum bump-increment. |br|
    The supported increments have this order: |br|
    'postrelease' < 'prerelease' < 'patch' < 'minor' < 'major'. |br|
    For an example, a value of 'patch' will prevent 'minor' or 'major' bumps,
    which may be handy to prevent accidental releases from maintenance
    branches. |br|
    Passing ``--force`` on the command line will allow to ignore this setting.

repo (str), *mandatory*
    GitHub repository name in the form 'USER/REPO', for example
    'mar10/test-release-tool'.

version (dict)
    Define the location of the project's version number. |br|
    See :ref:`version-locations-label` for details.


Tasks
=====

Common Task Options
-------------------
All tasks share these common arguments
(see also :class:`~yabs.task.common.WorkflowTask`):

dry_run (bool), default: *false*
    Run this task without really writing changes.
    This task-flag overrides the global mode, which is enabled using the
    ``--dry-run`` (or ``-n``) argument.

verbose (int), default: *3*
    Set log verbosity level in the range of quiet (0) to very verbose (5).
    This task-flag overrides the global mode, which is incremented/decremented
    using the ``--verbose``/``--quiet`` (or ``-n``/``-q``) arguments.


'build' Task
------------

This task calls ``python setup.py TARGET`` to create Python builds. The artifacts
are then typically used by following tasks like *pypi_release*. |br|
Technically, the files are first created in a temporary folder and then moved
to the project's ``/dist`` folder:

.. code-block:: yaml

    - task: build
      targets:
        - sdist
        - bdist_wheel

clean (bool), default: *true*
    Run ``python setup.py clean --all`` after the builds were created on order
    to cleanup the build/ folder.
revert_bump_on_error (bool), default: *true*
    Un-patch a previously bumped version number if an error occurred while
    running this build task.
    This may make it a bit easier to recover and cleanup manually.
targets (list), default: *['sdist', 'bdist_wheel']*
    Valid targets are "sdist", "bdist_wheel", and "bdist_msi".

Command Line Arguments:

    ``--dry-run``
        Build artifacts to temp folder, but do not copy them to dist/.


'bump' Task
-----------

This task increments the project's version number according to
`SemVer <https://semver.org>`_ by patching the respective text file.
Please read :ref:`version-locations-label` and
`After-Release Versions </en/latest/ug_tutorial.html#after-release-versions>`_
for details. |br|
Example: bump version according to the ``--inc`` command line argument:

.. code-block:: yaml

    - task: bump
      inc: null

Bump version for after-release status:

.. code-block:: yaml

    - task: bump
      inc: postrelease
      prerelease_prefix: "a"
      prerelease_start_idx: 1

check (bool), default: *true*
    If *true*, ``python setup.py --version`` is called after bumping the version
    and an error is raised if it does not match the expected value.

inc (str|null), default: *null*
    If *null*, the value that was passed as ``--inc`` argument on the command
    line is used. |br|
    Otherwise the value must be one of *major*, *minor*, *patch*,
    *postrelease*, or *prerelease*.

prerelease_prefix (str), default: *"a"*
    This value is used to prefix pre- or post-release version numbers.
    For example if ``"a"`` (the default) is passed, the pre-release version
    for ``1.2.3`` could be ``1.2.3-a1``.

prerelease_start_idx (int), default: *1*
    This value is used to prefix pre- or post-release version numbers.
    For example if ``0`` is passed, the pre-release version
    for ``1.2.3`` would be ``1.2.3-a0``.

Command Line Arguments:

    ``--dry-run``
        Calculate, but do not write the new version to the target file.
    ``--inc``
        Define the `SemVer <https://semver.org>`_ increment ('postrelease',
        'prerelease', 'patch', 'minor', or 'major'). |br|
        This arguemnt is only considered if the task defines the ``inc: null``
        option.
    ``--force``
        Bump version even if the max_increment rule would be violated.
    ``--force-pre-bump``
        Bump `--inc postrelease` even if the current version is untagged.
    ``--no-bump``
        Skip all *bump* tasks by forcing them to dry-run mode.


'check' Task
------------

This task will test a bunch of preconditons and stop the workflow if one or more
checks fail.

.. code-block:: yaml

    - task: check
      build: true             # dist/ folder exists
      can_push: true          # Test if 'git push' would succeed
      clean: true             # Repo must/must not contain modifications
      github: true            # GitHub repo name valid and online accessible
      os: null                # (str, list)
      pypi: true              # `twine` is available, PyPI package accessible
      python: ">=3.9"         # SemVer specifier
      up_to_date: true        # everything pulled from remote
      venv: true              # running inside a virtual environment
      version: true           # `setup.py --version` returns the configured version
      winget: true            # `wingetcreate` is available
      yabs: ">=0.5"           # SemVer specifier

build (bool), default: *true*
    Test if ``./dist`` folder exists.

can_push (bool), default: *true*
    Test if ``git push --dry-run`` would succeed.

clean (bool), default: *true*
    Test if the index or the working copy is clean, i.e. has no changes.

github (bool), default: *true*
    Test if the GitHub repository is accessible. This implies that

       - An internet connection is up
       - GitHub is reachable
       - The GitHub OAuth token (`config.gh_auth.oauth_token_var` option) is valid
       - The repository name (`config.repo` option) exists and is accessible

os (str | list), default: *null*
    Test if the return value of ``platform.system()`` is in the provided list. |br|
    Typical values are 'Linux', 'Darwin', 'Java', 'Windows'.

pypi (bool), default: *true*
    Test if `twine <https://twine.readthedocs.io>`_ is available, 
    `~/.pypirc <https://packaging.python.org/en/latest/specifications/pypirc/>`
    exists, and the package is registered at `PyPI <https://pypi.org/>`. |br|
    This is required by the *pypi_release* task.

python (str), default: *null*
    Test if the current Python version matches the provided specification. |br|
    Example ``python: '>=3.9'``

repo (str), default: *(value from config.repo)*
    Allows to override the global setting.

up_to_date (bool), default: *true*
    Test if the remote branch contains unpulled changes, by calling
    ``git status -uno``.

venv (bool), default: *true*
    Test if yabs is running inside a virtual environment.

version (bool), default: *true*
    Test if the result of ``python setup.py --version`` matches the version
    that yabs read from the configured version location.

winget (bool), default: *null* (depends)
    Test if ``wingetcreate.exe`` is installed (required by ``winget_release`` task). |br|
    Also pre-releases will be flagged.

    If `null` or undefined, this test is activated if a `winget_release` task
    is present and `--no-winget` is not passed.

yabs (str), default: *null*
    Test if the installed Yabs version matches the provided specification. |br|
    Example ``yabs: '>=0.5'``

Command Line Arguments:

    ``--no-check``
        Print warnings but continue workflow even if one or more checks failed.


'commit' Task
-------------

Commit modified files using ``git commit``:

.. code-block:: yaml

    - task: commit
      add_known: true
      message: |
        Bump version to {version}

add (list), default: *[]*
    Optional list of files and patterns to add to the index.

add_known (bool), default: *true*
    Commit with --all option (commit all changed files).

message (str), default: *'Bump version to {version}'*
    Commit message. |br|
    Context macros are expanded, e.g. '{version}', ...
    See :ref:`template-macros-label` for details. |br|
    Tip: when using `Travis <https://travis-ci.com>`_, a '[ci skip]' substring
    tells travis to ignore this commit.

Command Line Arguments:

    ``--dry-run``
        Pass ``--dry-run`` to git commands.


'exec' Task
-----------

Run a shell command using
`subprocess.run() <https://docs.python.org/3/library/subprocess.html#subprocess.run>`_,
for example ``tox -e lint``:

.. code-block:: yaml

    - task: exec
      args: ["tox", "-e", "lint"]
      always: true            # `true`: run even in dry-run mode
      silent: true            # `true`: suppress final printing of process output
      ignore_errors: false    # `true`: show warning, but proceed on errors (exit code != 0)
      timeout: 60.0           # Kill process after <n> seconds

add_artifacts (dict), default: *null*

    Check folder for files that were created by the shell command and add them 
    as artifact for downstream tasks.
    
    .. code-block:: yaml
    
    - add_artifacts:  # Add new files if any
      folder: "dist"  
      matches:
      bdist_msi: '.*\.msi'
   

args (list), mandatory
    List of command line parts.

always (bool), default: *false*
    If true, this command will also be run in dry-run mode.

dry_run_args (list), default: *null*
    List of command line parts that will be used instead of the `exec.args`
    option when dry-run mode is active. |br|
    Otherwise in dry-run mode only the command line args are printed.

ignore_errors (bool), default: *false*
    If true, error code != 0 will be ignored (yabs would stop otherwise).

log_start (bool), default: *true*
    If true, 'Running xxx...' is printed before calling the actual script.

silent (bool), default: *false*
    Controls whether the process output will be printed to the console *after*
    the command finished. |br|
    *false*: Always print output after the command finished. |br|
    *true*: Print output only when errors occured (return code != 0). |br|
    NOTE: A summary line is always printed. |br|
    NOTE: For long-running tasks, *streamed: true* may be a better option.

streamed (bool), default: *null*
    Poll and log output *while* the process is running. |br|
    *true* enable polling (mutually exclusive with *silent: false*). |br|
    *false* disable polling. |br|
    *null* assume *true* if verbose mode is on.

timeout (float), default: *null*
    Kill the subprocess after *timeout* seconds.

Command Line Arguments:

    ``--dry-run``
        Do not execute the shell command (see also `always` and `dry_run_args`
        above).


'github_release' Task
---------------------

Use the `GitHub API <https://docs.github.com/en/rest>`_ to create a release
from the tag and artifacts that yabs created in previous tasks:

.. code-block:: yaml

    - task: github_release
      name: 'v{version}'
      message: |
        Released {version}

        [Changelog](https://github.com/{repo}/blob/master/CHANGELOG.md),
        [Commit details](https://github.com/{repo}/compare/{org_tag_name}...{tag_name}).
      prerelease: null  # null: guess from version number format
      upload:
        - sdist
        - bdist_wheel

gh_auth (dict), default: *null*
    Optionally override the global `config.gh_auth` setting.

draft (bool), default: *false*
    *true*: create a draft (unpublished) release |br|
    *false*: to create a published one. |br|
    Use the ``--gh-draft`` argument to override.

message (str), default: *'(see example above)'*
    Description of the release.
    See also :ref:`template-macros-label`.

name (str), default: *'v{version}'*
    The name of the new release.
    See also :ref:`template-macros-label`.

prerelease (bool), default: *null*
    *false*: mark as full release. |br|
    *true*: mark as pre-release, i.e. not ready for production and may be unstable. |br|
    *null*: guess from version number, i.e. post-release numbers containing '-'
    are considered pre-releases. |br|
    Use the ``--gh-pre`` to argument to override.

repo (str), default: *null*
    Optionally override the global `config.repo` setting.

.. tag (str), default: *null*
..     description.

target_commitish (str), default: *null*
    Specifies the commitish value that determines where the Git tag is created
    from. Can be any branch or commit SHA.
    Unused if the Git tag already exists. |br|
    Default: the repository's default branch (usually master).

upload (list), default: *null*
    List of artifact names ('sdist', 'bdist_wheel', and 'bdist_msi'). |br|
    Default *null*: upload all artifacts that were created in the previous
    build-task.

Command Line Arguments:

    ``--dry-run``
        Do not actually call the GitHub API request.
    ``--gh-draft``
        Force `github_release.draft: true`.
    ``--gh-pre``
        Force `github_release.prerelease: true`.
    ``--no-release``
        Skip this task.

**Preconditions**

A *tag* and *build* task must be run first.


'push' Task
-----------

Call ``git push`` to push changes and tags:

.. code-block:: yaml

    - task: push
      tags: true

tags (bool), default: *false*
    Use ``--follow-tags`` to push annotated tags as well.

target (str), default: *''*
    Defines the push target. |br|
    By default, the 'branch.*.remote' configuration for the current branch is
    consulted. If the configuration is missing, it defaults to 'origin'.

Command Line Arguments:

    ``--dry-run``
        Pass '--dry-run' option to 'git push' command.


'pypi_release' Task
-------------------

Call ``twine upload`` create a release on `PyPI <https://pypi.org>`_ from the
artifacts that yabs created in previous tasks:

.. code-block:: yaml

    - task: pypi_release

comment (str), default: *null*
    Optional string passed as `twine --comment COMMENT ...`.

upload (list), default: *null*
    List of artifact names ('sdist', 'bdist_wheel', and 'bdist_msi'). |br|
    Default *null*: upload all artifacts that were created in the previous
    build-task.

Command Line Arguments:

    ``--dry-run``
        description.
    ``--no-release``
        Skip this task.

**Preconditions**

- A *tag* and *build* task must be run first.
- `twine <https://twine.readthedocs.io>`_ must be available.


'tag' Task
----------

Call ``git tag`` to create an annotated tag:

.. code-block:: yaml

    - task: tag
      name: v{version}
      message: |
        Version {version}

message (str), default: *'Version {version}'*
    The description of the new tag.
    See also :ref:`template-macros-label`.

name (str), default: *'v{version}'*
    The name of the new tag.
    See also :ref:`template-macros-label`.

Command Line Arguments:

    ``--dry-run``
        description.


'winget_release' Task
---------------------

Call ``wingetcreate update`` to update an existing 
`release on winget-pkgs <https://github.com/microsoft/winget-pkgs>`_:

.. code-block:: yaml

    - task: winget_release
      upload: 'bdist_msi'
      package_id: 'foo.bar'
      assume_synced: false 

assume_synced (bool), default: *false*
    If true, skip warning about outdated fork.

package_id (str)
    Package id in the WPM repo. Typically USER.PROJECT.

upload (str), default: *'bdist_msi'*
    The artifact-id that was created using an upstream exec task.


Command Line Arguments:

    ``--dry-run``
        description.
