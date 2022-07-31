Installation
============

Requirements: `Python <https://www.python.org/downloads/>`_ 3.7+ is required.
Releases are hosted on `PyPI <https://pypi.python.org/pypi/yabs>`_ and can
be installed using
`pip <https://pip.pypa.io/en/stable>`_
or `pipenv <https://pipenv.pypa.io/>`_.

.. .. note::
..   MS Windows users that only need the command line interface may prefer the
..   `MSI installer <https://github.com/mar10/yabs/releases>`_.

Install Into the System Python
------------------------------

Installing `yabs` as part of your system's Python will make the |CLI|
available from the command line.
You may need administrator permissions, like ``sudo``.
Also make sure to use Python 3 if the system installation uses Python 2
(as on macOS).

For example::

  $ sudo python3 -m pip install -U yabs
  $ yabs --version -v
  yabs/1.0.0 Python/3.6.1 Darwin-17.6.0-x86_64-i386-64bit
  $ yabs --help
  ...

Run From a Virtual Environment
------------------------------

Installing `yabs` and its dependencies into a 'sandbox' will help to keep
your system Python clean, but requires to activate the virtual environment::

  $ cd /path/to/yabs
  $ pipenv shell
  (yabs) $ pipenv install yabs --upgrade
  (yabs) $ yabs --version -v
  yabs/0.0.1 Python/3.6.1 Darwin-17.6.0-x86_64-i386-64bit
  (yabs) $ yabs --help
  ...

.. seealso::
   See :doc:`development` for directions for contributors.

Now the ``yabs`` command is available::

  $ yabs --help

and the ``yabs`` package can be used in Python code::

  $ python
  >>> from yabs import __version__
  >>> __version__
  '0.0.1'
