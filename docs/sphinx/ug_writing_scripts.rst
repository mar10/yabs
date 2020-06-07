---------------
Writing Scripts
---------------

Overview
========

Run configuration scripts are text files, that are read and compiled by the
*Context Manager*. This configuration is then passed to the *Run Manager*
for execution.

.. note::

    Unless you are a Python programmer, you may have to get used to the fact
    that **whitespace matters** in YAML files: |br|
    Make sure you indent uniformly. Don't mix tabs and spaces.
    We recommend to use an editor that supports the YAML syntax (e.g. VS Code).

A simple confuguration script may look like this: |br|
``yabs.yaml``:

.. literalinclude:: yabs_minimal.yaml
    :linenos:
    :language: yaml


Task Types
==========

See reference: TODO

Template Macros
===============

See reference: TODO

Versions
========

Pre-Releases
------------

See also [PEP 440](https://www.python.org/dev/peps/pep-0440/#id27).

Version Locations
-----------------

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

**Note:** YAML assumes that a version number consists of three parts and
optional extension, as described in [Semantic Versioning](https://semver.org).

`pyproject.toml` in the project's root folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

`__init__.py` of the project's root package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

A Plain Text File
~~~~~~~~~~~~~~~~~
For example a `_version.txt` file in the procect's `src` folder containing:
```py
1.2.3
```
can be configured in `yabs.yaml` like so:
```yaml
- file: src/version.txt
  template:
```


`setup.cfg` of the project's root folder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

Debugging
=========

Use the ``--verbose`` (short ``-v``) option to generate more console logging. |br|
Use the ``--dry-run`` (short ``-n``) option to run all tasks in a simulation mode::

    $ yabs run --inc patch -vn

The `monitor` argument will add the activity as distinct entry of a special
section of the monitor dashboard (use with the ``--monitor`` option):

.. code-block:: yaml

    sequences:
      main:
        - activity: GetRequest
          url: $(base_url)/
          assert_match: ".*Index of /.*"
          assert_html:
            "//*[@class='logo']": true
          debug: true
          monitor: true
