# ![logo](https://raw.githubusercontent.com/mar10/yabs/master/docs/sphinx/yabs_48x48.png) yabs

> Test, Build, Deliver!

[![Build Status](https://travis-ci.org/mar10/yabs.svg?branch=master)](https://travis-ci.org/mar10/yabs)
[![Latest Version](https://img.shields.io/pypi/v/yabs.svg)](https://pypi.python.org/pypi/yabs/)
[![License](https://img.shields.io/pypi/l/yabs.svg)](https://github.com/mar10/yabs/blob/master/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/yabs/badge/?version=latest)](https://yabs.readthedocs.io/)
[![Coverage Status](https://coveralls.io/repos/github/mar10/yabs/badge.svg?branch=master)](https://coveralls.io/github/mar10/yabs?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![StackOverflow: yabs](https://img.shields.io/badge/StackOverflow-yabs-blue.svg)](https://stackoverflow.com/questions/tagged/yabs)


## Overview

Build and deployment automation for Python projects.

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

Custom tasks may be added using the plugin framework.

[Read the documentation](https://yabs.readthedocs.io/en/latest/ug_tutorial.html)
for details.


## Preconditions

- Use [git](https://git-scm.com), [PyPI](https://pypi.org) and [GitHub](https://github.com).
- Version numbers follow roughly the [Semantic Versioning](https://semver.org) pattern.
- The project's version number is maintained in
  [one of the supported locations](https://yabs.readthedocs.io/)

(See [grunt-yabs](https://github.com/mar10/grunt-yabs) for a node.js variant
if you have a JavaScript based development stack.)
