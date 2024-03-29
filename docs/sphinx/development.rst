===========
Development
===========

Install for Development
=======================

First off, thanks for taking the time to contribute!

This small guideline may help taking the first steps.

Happy hacking :)


Fork the Repository
-------------------

Clone yabs to a local folder and checkout the branch you want to work on::

    $ git clone git@github.com:mar10/yabs.git
    $ cd yabs
    $ git checkout my_branch


Work in a Virtual Environment
-----------------------------

Install Python
^^^^^^^^^^^^^^
We need `Python 3.7+ <https://www.python.org/downloads/>`_,
and `pipenv <https://pipenv.pypa.io/>`_ on our system.

If you want to run tests on *all* supported platforms, install Python
3.7, 3.8, 3.9, 3.10, and 3.11.

Create and Activate the Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install dependencies for debugging::

    $ cd /path/to/yabs
    $ pipenv shell
    (yabs) $ pipenv install --dev
    (yabs) $

The development requirements already contain the yabs source folder, so
``pipenv install -e .`` is not required.

The code should now run::

    $ yabs --version
    2.0.0

The test suite should run as well::

    $ tox

Build Sphinx documentation to target: `<yabs>/docs/sphinx-build/index.html`) ::

    $ tox -e docs


Run Tests
=========

Run all tests with coverage report. Results are written to <yabs>/htmlcov/index.html::

    $ tox

Run selective tests::

    $ tox -e py37
    $ tox -e py37 -- -k test_context_manager


Code
====

The tests also check for `eslint <https://eslint.org>`_,
`flake8 <http://flake8.pycqa.org/>`_,
`black <https://black.readthedocs.io/>`_,
and `isort <https://github.com/timothycrosley/isort>`_ standards.

Format code using the editor's formatting options or like so::

    $ tox -e format


.. note::

    	Follow the Style Guide, basically
        `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_.

        Failing tests or not follwing PEP 8 will break builds on
        `travis <https://travis-ci.com/github/mar10/yabs>`_,
        so run ``$ tox`` and ``$ tox -e format`` frequently and before
        you commit!


Create a Pull Request
=====================

.. todo::

    	TODO
