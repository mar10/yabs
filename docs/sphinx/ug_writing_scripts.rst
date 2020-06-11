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

.. todo::
  Documentation missing.


Template Macros
===============

.. todo::
  Documentation missing.


Version Locations
=================

(**TODO:** verify this section.)

Although there seems to be consent that Python projects should have a version
number that is stored at *one* central location, the community has not agreed
upon that location yet.

In order to find and bump this versions, we need to pass a hint in
the configuration `yabs.yaml` like so:

.. code-block:: yaml

    file_version: yabs#1
    config:
      ...
      version:
        - type: __version__  # Example!
          file: src/my_project/__init__.py
    ...

Yabs supports some common approaches. |br|
Following some typical patterns how Python projects store version numbers.

.. note::
  Currently we would recommend this variant (unless Poetry is used): |br|
  Store the version in ``__init__.py`` of the project's root folder::

    __version__ = "1.2.3"

  Then reference this in ``setup.cfg``::

    [metadata]
    name = my_package
    version = attr: my_project.__version__


See below for different use cases.

Poetry
------

.. todo::
  Not yet implemented.

`Poetry <https://python-poetry.org/docs/pyproject/#version>`_ stores the version
number in its own section in ``pyproject.toml``
(defined in `PEP-518 <https://www.python.org/dev/peps/pep-0518/>`_):

``pyproject.toml``:

.. code-block:: toml

    [project]
    ...
    [tool.poetry]
    name = "my_project"
    version =  "1.2.3"

``yabs.yaml``:

.. code-block:: yaml

    config:
      version:
        - type: poetry


flit
----

.. todo::
  Not yet implemented.


__init__.py of the project's root package
-----------------------------------------

``__init__.py``::

    __version__ = "1.2.3"

``yabs.yaml``:

.. code-block:: yaml

    config:
      version:
        - type: __version__
          file: src/my_project/__init__.py

Or a variant the mimics Python's `sys.version_info` style:

``__init__.py``::

    version_info = (1, 2, 3)
    version = ".".join(str(c) for c in version_info)

``yabs.yaml``:

.. code-block:: yaml

    config:
      version:
        # TODO

Plain Text File
---------------

For example a `_version.txt` file in the project's `src` folder containing:

``_version.txt``::

    1.2.3

``yabs.yaml``:

.. code-block:: yaml

    config:
      version:
        # TODO


setup.cfg
---------

See also `PEP-396 <https://www.python.org/dev/peps/pep-0396/#distutils2>`_
and `setuptools <https://setuptools.readthedocs.io/en/latest/setuptools.html#id47>`_ .

``setup.cfg`` in the project's root folder:

.. code-block:: ini

    [metadata]
    name = my_package
    version = 1.2.3

``yabs.yaml``:

.. code-block:: yaml

    config:
      version:
        # TODO

The follwing two examples for setup.cfg use the special ``attr:`` and ``file:``
directives that where introduced with
`setuptools v39.2 <https://setuptools.readthedocs.io/en/latest/setuptools.html#metadata>`_ ).

**Note:** This assumes that the version is stored in a separate text- or Python file,
which is covered in the examples above.

.. code-block:: ini

    [metadata]
    name = my_package
    version = attr: my_project.__version__

.. code-block:: ini

    [metadata]
    name = my_package
    version = file: path/to/file

The follwing two examples for setup.cfg use the special ``version-file`` and
``version-from-file`` options that where proposed for
`distutils2 <https://www.python.org/dev/peps/pep-0396/#distutils2>`_.

**Note:** This assumes that the version is stored in a separate text- or Python file,
which is covered in the examples above.

.. code-block:: ini

    [metadata]
    # The entire contents of the file contains the version number
    version-file = version.txt

.. code-block:: ini

    [metadata]
    # The version number is contained within a larger file, e.g. of Python code,
    # such that the file must be parsed to extract the version
    version-from-file = elle.py


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
