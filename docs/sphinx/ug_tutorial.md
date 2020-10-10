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
8. Bump, tag, commit, and push for post-release.

Some **preconditions** are assumed:

- We use [git](https://git-scm.com), [PyPI](https://pypi.org) and [GitHub](https://github.com).
- Version numbers follow roughly the [Semantic Versioning](https://semver.org) pattern.
- The project's version number is maintained in
  [one of the supported locations](#versions).

**Note:**<br>
Yabs can be extended using the [plugin API](ug_writing_plugins.html).


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

tasks:
  - task: check
    branches: master
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

See [Writing Scripts](ug_writing_scripts.html) for details.


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
black = "==19.10b0"
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

(**TODO:** verify this section.)

After a new release was published, we should do another bump.
This will make sure that any following code change is not accidently
associated with the public tag name.

This *after-release* version number should

- have a higher sort order than the previous release, i.e. compare
  *greater than* (`>`) our current release
- however the increment should be small, since we should never *de*crement a
  version number, and we don't know by now if the next release will
  contain major-, minor-, or patch-level changes
- have a format that indicates a *preliminary* status
  (i.e. not be installed, unless `--pre` is passed to `pip`)

[SemVer does support pre-releases](https://semver.org/#spec-item-9), but not
post-releases ([only build metadata, which is not sortable](https://semver.org/#spec-item-10)).<br>
Pre-releases are considered 'unstable', which is what we want to signal until
we make the next release.

[PEP 440 supports](https://www.python.org/dev/peps/pep-0440/#id27) pre-, post-,
and developmental releases.

Yabs suggests this pattern:
> After a release, bump & commit a patch-incremented version with pre-release
> appendix, for example:<br>
> `v1.2.3` &#x21d2; `v1.2.4a1`<br>
> The next release will be a patch, minor, or major increment, which brings us
> to <br>
> &#x21d2; `v1.2.4`, `v1.3.0`, or `v2.0.0`.


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
See [Writing Scripts](ug_writing_scripts.html) for details.
