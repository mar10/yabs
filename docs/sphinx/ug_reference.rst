----------------
Script Reference
----------------

Workflow Configuration
======================

.. code-block:: yaml

    config:
      # Options used as default for all following tasks in this workflow
      repo: 'mar10/test-release-tool'
      gh_auth:
        oauth_token_var: GITHUB_OAUTH_TOKEN
      version:
        - type: __version__
          file: src/test_release_tool/__init__.py
      max_increment: minor
      branches:
        - master

repo
    'mar10/test-release-tool'
gh_auth:
    oauth_token_var: GITHUB_OAUTH_TOKEN
version:
    - type: __version__        # First entry is master for synchronizing
        file: src/test_release_tool/__init__.py
        # match: '__version__\s*=\s*[''\"](\d+\.\d+\.\d+).*[''\"]'
        # template: '__version__ = "{version}"'
        # - type: setup_cfg        # First entry is master for synchronizing
        #  entry: metadata.version
        #  template:
max_increment:
    minor
branches:
    # Allowed git branches
    - master


Tasks
=====

Common Task Options
-------------------
All activites share these common arguments
(see also :class:`~yabs.cmd_common.WorkflowTask`).

verbose (int, optional)
    Default: 3
dry_run (bool, optional)
    Default: false, except for `Sleep` activities

'bump' Task
-----------

.. code-block:: yaml

   - task: bump
     inc: null
     check: false
     prerelease_prefix: "a"

inc (str|null), optional, default: *null*
    If *null*, the value that was passed as ``--inc`` argument on the command
    line is used.
    Otherwise the value must be one of *major*, *minor*, *patch*,
    *postrelease*, or *prerelease*.

check (bool), optional, default: *false*
    If *true*, ``setup.py --version`` is called after bumping the version and
    an error is raised if it does not match the expected value.

prerelease_prefix (str), optional, default: *"a"*
    This value is used to prefix pre- or post-release version numbers.
    For example if ``"a"`` (the default) is passed, the pre-release version
    for ``1.2.3`` could be ``1.2.3-a0``.

(see also :class:`~yabs.cmd_bump.BumpTask`).

