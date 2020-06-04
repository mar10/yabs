# Tutorial

## Overview

*yabs* is a tool, that runs a sequence of tasks in order to test, build, and
deliver a Python software project.

The workflow is defined in a configuration file, using a simple YAML format and can be executed like

```bash
$ yabs run --inc minor
```

The example above assumes that the config file is found at the default location `./yabs.yaml`. The workflow refers to the `--inc` argument for the 'bump' task (in this case a [minor version increment](https://semver.org/)).

A typical release workflow may look like this:

1. Check preconditions: *Is the workspace clean, anything to commit?*,
   *Is GitHub reachable?*, *Are we on the correct branch?*, ...
2. Make sure static code linters and unit tests pass.
3. Bump the project's version number (major, minor, or patch, according to
   [Semantic Versioning](https://semver.org)). <br>
   Then patch the version string into the respective Python module or text file.
4. Build *sdist* and *wheel* assets.
5. Tag the version, commit, and push.
6. Upload distribution to [PyPI](https://pypi.org).
7. Create a new release on [GitHub](https://github.com) and upload assets.
8. Bump, tag, commit, and push for post-release.

Some **preconditions** are assumed:

- Use [git](https://git-scm.com), [PyPI](https://pypi.org) and [GitHub](https://github.com).
- Version numbers follow roughly the [Semantic Versioning](https://semver.org) pattern.
- The project's version number is maintained in
  [one of the supported locations](#versions).


## Workflow Definition

A **run configuration** describes all aspects of a test suite. It defines one
*scenario* and additional options.

A **scenario** defines a list of *sequences* that are executed in order,
possibly looping. Think of it as a kind of story book that describes one user's
behavior. |br|
During a run, the scenario is executed in one or more parallel user *sessions*.

**Sequences** are lists of *activities* that are executed in order.
Sequences named 'init' and 'end' are typically reserved to set-up and tear-down
scenarios. Often we have a looping 'main' sequence in the middle, but we
can define more sequences with arbitrary names.

**Activities** are the smallest building blocks of scenarios.
Typical activies are `GetRequest`, `PutRequest`, `RunScript`, `Sleep`, ... |br|
Every activity can be configured, for example with a request URL and
parameters, checks for expected results, etc. |br|
Custom **plugins** can be developed and installed to make additional activities
available.

While the *scenario* is executed, a dictionary of global variables is
available. Activities can access this **context** in order to read
configuration or pass information along.

**Macros** are used in activity definitions to pass *context* variables as
options.

When a scenario is run, one or more  **sessions** are executed in parallel.
Every session has a virtual *user* assigned.

The **command line interface** (CLI) can be run from the computer console. It
will read and compile the configuration file, execute the scenario, and display
results and statistics. |br|
Alternativly include the **Python `yabs` package** in your project, define,
configure, and run the scenario programmatically.

The *CLI* can open a **monitor** application that displays the current
execution statistics in real time.


## Versions

See also [PEP 440](https://www.python.org/dev/peps/pep-0440/).

### Pre-Releases

See also [PEP 440](https://www.python.org/dev/peps/pep-0440/#id27).

### Different Version Locations


Following some typical patterns how Python projects store version numbers.
In order for YAML to find and bump this versions, we need to pass a hint in
the YAML configuration can be configured in `yabs.yaml` like so:
```yaml
file_version: yabs#1
config:
  ...
  version:
    - mode: pyproject
...
```


**Note:** YAML assumes that a version number consists of three parts and optional
extension, as described in [Semantic Versioning](https://semver.org).

#### `pyproject.toml` in the project's root folder

```toml
[project]
name = "my_project"
version =  "1.2.3"
```
can be configured in `yabs.yaml` like so:
```yaml
config:
  version:
    - mode: pyproject
```

#### `__init__.py` of the project's root package

```py
__version__ = "1.2.3"
```
can be configured in `yabs.yaml` like so:
```yaml
- file: setup.cfg
  entry: metadata.version
  template:
```
Or a variant the mimics Python's `sys.version_info` style:
```py
version_info = (1, 2, 3)
version = ".".join(str(c) for c in version_info)
```
can be configured in `yabs.yaml` like so:
```yaml
- file: setup.cfg
  entry: metadata.version
  template:
```

#### A Plain Text File
For example a `_version.txt` file in the procect's `src` folder containing:
```py
1.2.3
```
can be configured in `yabs.yaml` like so:
```yaml
- file: src/version.txt
  template:
```


#### `setup.cfg` of the project's root folder
See also [PEP-396](https://www.python.org/dev/peps/pep-0396/#distutils2) and [setuptools](https://setuptools.readthedocs.io/en/latest/setuptools.html#id47).
```ini
[metadata]
name = my_package
version = 1.2.3
```
can be configured in `yabs.yaml` like so:
```yaml
- file: setup.cfg
  entry: metadata.version
  template:
```

However the follwing examples for setup.cfg assume that the version is stored
in a separate text or Python file, which is covered above:
```ini
[metadata]
name = my_package
version = attr: src.VERSION
```
```ini
[metadata]
version-file = version.txt
```
```ini
[metadata]
version-from-file = elle.py
```
