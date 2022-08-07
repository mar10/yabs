# Tutorial

## Overview

*Yabs* is a command line tool, that runs a sequence of tasks in order to test,
build, and deliver a Python software project.

The workflow is defined in a configuration file, using a simple YAML format and
can be executed like

```bash
$ yabs run --inc minor
```

The example above assumes that the config file is found at the default location
`./yabs.yaml`. The workflow refers to the `--inc` argument for the 'bump' task
(in this case a [minor version increment](https://semver.org/)).

A typical release workflow may look like this:

1. Check preconditions: *Is the workspace clean, anything to commit?*,
   *Is GitHub reachable?*, *Are we on the correct branch?*, ...
2. Make sure that static code linters and unit tests pass, run [tox](https://tox.readthedocs.io/).
3. Bump the project's version number (major, minor, or patch, according to
   [Semantic Versioning](https://semver.org)). <br>
   Then patch the version string into the respective Python module or text file.
4. Build *sdist* and *wheel* assets.
5. Tag the version, commit, and push.
6. Upload distribution to [PyPI](https://pypi.org).
7. Create a new release on [GitHub](https://github.com) and upload assets.
8. Create a new release on the 
   [Windows Packager Manager Repository](https://github.com/microsoft/winget-pkgs).
9. Bump, tag, commit, and push for post-release.


Some **preconditions** are assumed:

- We use [git](https://git-scm.com), [PyPI](https://pypi.org) and [GitHub](https://github.com).
- Version numbers follow roughly the [Semantic Versioning](https://semver.org) pattern.
- The project's version number is maintained in
  [one of the supported locations](#versions).

**Note:**<br>
Yabs can be extended using the [plugin API](ug_writing_plugins.rst).


## Workflow Definition

A **workflow definition** is a [YAML](https://en.wikipedia.org/wiki/YAML) file
that defines some general settings and a sequence of *tasks*.

**Tasks** are the building blocks of a workflow. They have a type name and
additonal parameters.

The internal **Task Runner** executes the task sequence and passes a
**Task Context** along. This allows an upstream task to pass information
downstream. For examle a *bump* task will set a new version number that may be
used in a commit message *template*.

Some string parameters are evaluated as **template**, i.e. included *macros*,
like `"{version}"`, are expanded.

`yabs.yaml`:
```yaml
file_version: yabs#1
config:
  repo: 'mar10/test-release-tool'
  version:
    # Location of the project's version:
    - type: __version__
      file: src/test_release_tool/__init__.py
  branches:  # Allowed git branches
    - master

tasks:
  - task: check
    github: true
    clean: true

  - task: exec
    args: ["tox", "-e", "lint"]
    always: true

  - task: bump  # bump version according to `--inc` argument

  - task: commit
    message: |
      Bump version to {version}

  - ...
```

See [Writing Scripts](ug_writing_scripts.rst) for details.


## Versions

Python projects should have a version number that is stored at *one* central
location.<br>
This version number will appear in the about box, when a CLI is called with
a `--version` argument, when `setup.py --version` is called, etc.<br>
Most importantly, it is used to generate tag names, that uniquely identify
[PyPI](https://pypi.org) releases.

Especially when our  project is a kind of a library that other projects may
depend on, incrementing ('bumping') the version number is an important step in
the release process.<br>
Installation tools like [pip](https://pip.pypa.io/) and
[Pipenv](https://pipenv.pypa.io/) rely heavily on consistent version number
schemes, when defining requirements:

```ini
[dev-packages]
black = "~=22.1"
tox = "~=3.2"
[packages]
PyYAML = "~=5.2"
...
```

See also [PEP 440](https://www.python.org/dev/peps/pep-0440/).<br>
Yabs assumes that a version number consists of three parts and optional
extension, as described in [Semantic Versioning](https://semver.org),
e.g. `"1.2.3"`, `"1.2.4-a1"`.


### After-Release Versions

After a new release was published, we should commit and push another bump.
This will make sure that any following code change is not accidently
associated with the public tag name.

This *after-release* version number should

- have a higher sort order than the previous release, i.e. compare
  *greater than* (`>`) our current release
- however the increment should be small, since we should never *de*crement a
  version number (even if not tagged yet), and we don't know by now if the next 
  release will contain major-, minor-, or patch-level changes
- have a format that indicates a *preliminary* status
  (i.e. not be installed, unless `--pre` is passed to `pip`)

[PEP 440 supports](https://www.python.org/dev/peps/pep-0440/#id27) pre-, post-,
and developmental releases.

However [SemVer does support pre-releases](https://semver.org/#spec-item-9), 
but not post-releases ([only build metadata, which is not sortable](https://semver.org/#spec-item-10)).<br>
Pre-releases are considered 'unstable', which is what we want until we make the 
next release.

Yabs suggests this pattern:
> After a release, bump, commit, and push a patch-incremented version with 
> pre-release appendix, for example:<br>
> `v1.2.3` &#x21d2; `v1.2.4-a1`<br>
> The next release will be a patch, minor, or major increment, which brings us
> to <br>
> &#x21d2; `v1.2.4`, `v1.3.0`, or `v2.0.0`.

The `--inc postrelease` pseudo bump increment will handle these cases.


### General Bump Rules

For example, running 
```bash
$ yabs run --inc INCREMENT
```
will yield these results:

| Existing Tag | Existing Version | Bump Increment | New Version                |
| ------------ | ---------------- | -------------- | -------------------------- |
| Initial                                                                       |
| n.a.         | `<none>`         | major          | `1.0.0`                    |
| n.a.         | `<none>`         | minor          | `0.1.0`                    |
| n.a.         | `<none>`         | patch          | `0.0.1`                    |
| n.a.         | `<none>`         | postrelease    | `0.0.1-a1` (1)             |
| After first run                                                               |
| ?            | `0.0.1-a1`       | major          | `1.0.0` (2)                |
| ?            | `0.0.1-a1`       | minor          | `0.1.0` (2)                |
| ?            | `0.0.1-a1`       | patch          | `0.0.1` (3)                |
| ?            | `0.0.1-a1`       | postrelease    | `0.0.1-a1` or `...-a2` (4) |
| After a release                                                               |
| `1.2.3`      | `1.2.4-a1`       | major          | `2.0.0` (2)                |
| `1.2.3`      | `1.2.4-a1`       | minor          | `1.3.0` (2)                |
| `1.2.3`      | `1.2.4-a1`       | patch          | `1.2.4` (3)                |
| `1.2.3`      | `1.2.4-a1`       | postrelease    | `1.2.4-a1` or `...-a2` (4) |


Remarks:

1. If no release is defined yet, `--inc postrelease` starts with `0.0.1-a1`.
2. Bump `major`, `minor` will increment the version and remove the 
   pre-release suffix if any.
3. Bump `patch` will simply remove the pre-release suffix, if one is set.<br>
   This is usuallay the case after a new release was published using a typical
   *Yabs* workflow, which ends with a post-release bump.

   If no pre-release suffix existed, the PATCH version is incremented.
4. `--inc postrelease` will increment the version depending on the current 
   situation:

   - If the current release was not a pre-release, the PATCH version is 
     incremented and the suffix is set to `a1`:<br>
     `v1.2.3` &#x21d2; `v1.2.4-a1`

   - If the current version is a pre-release, the suffix is incremented:<br>
     `v1.2.3-a1` &#x21d2; `v1.2.3-a2`
  
   - Special case:<br>
     If the current version is an **untagged** pre-release and the workflow
     task is the initial bump (with no explicit `inc: INC` setting) like so

      ```yaml
          # 'bump': Increment project version (requires argument: `yabs run --inc INC`)
        - task: bump
          inc: null  # Use value passed as 'yabs run --inc INC'
      ```
     
     then `--inc postrelease` will **not** tag:<br>
     `v1.2.3-a1` &#x21d2; `v1.2.3-a1`

     Reason: we assume that `1.2.3` is already released and follwoing workflow
     steps will tag and release `v1.2.3-a1` (which does not yet exist).
     Otherwise `...-a2` would be released, leaving a gap in the tag sequence.

     Pass `--force-pre-bump` to bump to `v1.2.3-a2` anyway.



### Version Locations

Although there seems to be consent that Python projects should have a version
number that is stored at *one* central location, the community has not agreed
upon that location yet.

Yabs supports some common approaches, that you can configure under
`config.version`, for example:

`yabs.yaml`:
```yaml
file_version: yabs#1
config:
  ...
   version:
     - type: __version__
       file: src/test_release_tool/__init__.py
 ...
```
See [Writing Scripts](ug_writing_scripts.rst) for details.


## Windows Package Manager

### Create the Initial Windows Package Manager Release

  MSI installers can only be created on Windows platforms.
  Also pre-releases are not allowed.

  Pass `--no-winget` to skip building and uploading an MSI installer 
  to the winget-pkgs repository.

  1. Run on Windows, make sure all tests pass.
     Create an MSI installer:
     ```ps1
     > tox
     > python -m setup_bdist_msi.py bdist_msi
     ```
     Since we have a pre-release, the installer will not have a real version, so
     uploading to *WPM* would fail!

     **Install and test** the MSI installer anyway:
     ```ps1
     > dist/yabs_test-0.0.0.0-win64.msi`
     ```

     **NOTE:** Publishing a pre-release and test the MSI that was uploaded to 
     GitHub (still version '0.0.0.0') may be a good idea before taking the 
     next step.
  
  2. Release a package with MSI installer:
     - Pre-releases (`--inc postrelease`) are **not allowed** here!<br>
       Make a *real* version: 
       The version increment must tbe at least `--inc patch`.
       
     - Pass `--no-winget-release` to prevent uploading (which would fail)

     Example:
     ```ps1
     > yabs run --inc patch --no-winget-release
     ```

     We should now have GitHub release with an additional MSI asset, e.g.
     `yabs_test-0.2.8.0-win64.msi`

  3. Test the MSI installer. The program version must match the tagged release 
     version.
  
  4. Create the initial manifest
     Since the token is probably already set as environment variable 
     for *Yabs* workflows, we can reference it here

     ```ps1
     > wingetcreate new --token $env:GITHUB_OAUTH_TOKEN https://github.com/USER/PROJECT/releases/download/v1.2.3/yabs_test-1.2.3.0-win64.msi
     ```

     The manifest can now be edited and sumbitted again like so:
     ```ps1
     > wingetcreate submit --token $env:GITHUB_OAUTH_TOKEN .\manifests\m\USER\PROJECT\1.2.3.0\
     ```

  5. There is no need to commit the manifest to Git:
     Add `manifests/` folder to `.gitignore`

  ...


### Create a Regular Windows Package Manager Release

Once a release exists on Windows Package Manager, Yabs can update releases
as part of the workflow:

```ps1
> yabs run --inc patch
```

> **Note**: Pre-releases (`--inc postrelease`) are still not allowed.<br>
> Make a *real* version: The version increment must tbe at least `--inc patch`.

```ps1
wingetcreate update --token $env:GITHUB_OAUTH_TOKEN --urls https://github.com/mar10/wsgidav/releases/download/v4.0.2/WsgiDAV-4.0.2.0-win64.msi --version 4.0.2.0 mar10.wsgidav
```
