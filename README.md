# ![logo](https://raw.githubusercontent.com/mar10/yabs/master/docs/sphinx/yabs_48x48.png) yabs

> Test, Build, Deliver!

[![Build Status](https://travis-ci.org/mar10/yabs.svg?branch=master)](https://travis-ci.org/mar10/yabs)
[![Latest Version](https://img.shields.io/pypi/v/yabs.svg)](https://pypi.python.org/pypi/yabs/)
[![License](https://img.shields.io/pypi/l/yabs.svg)](https://github.com/mar10/yabs/blob/master/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/yabs/badge/?version=latest)](https://yabs.readthedocs.io/)
[![Coverage Status](https://coveralls.io/repos/github/mar10/yabs/badge.svg?branch=master)](https://coveralls.io/github/mar10/yabs?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![StackOverflow: yabs](https://img.shields.io/badge/StackOverflow-yabs-blue.svg)](https://stackoverflow.com/questions/tagged/yabs)


(See [grunt-yabs](https://github.com/mar10/grunt-yabs) for a JavaScript-based variant.)

## Preconditions

- Use [git](https://git-scm.com), [PyPI](https://pypi.org) and [GitHub](https://github.com).
- Version numbers follow roughly the [Semantic Versioning](https://semver.org) pattern.
- The project's version number is maintained in
  [one of the supported locations](https://yabs.readthedocs.io/)


## Different Version Locations

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

### `pyproject.toml` in the project's root folder

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

### `__init__.py` of the project's root package

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

### A Plain Text File
For example a `_version.txt` file in the procect's `src` folder containing:
```py
1.2.3
```
can be configured in `yabs.yaml` like so:
```yaml
- file: src/version.txt
  template:
```


### `setup.cfg` of the project's root folder
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
