============
Architecture
============

..
    .. toctree::
    :hidden:


.. Overview
.. ========

.. |yabs| is a tool, that runs a sequence of tasks om order to test, build, and
.. deliver a Python software project. |br|
.. The workflow is defined in a configuration file, using a simple YAML format.


.. Concepts
.. ========

.. The :class:`yabs.task_runner.TaskRunner` ...

..   - Run manager
..   - Session manager
..   - Config manager


Class Overview
==============

General Classes
---------------

.. inheritance-diagram:: yabs.task_runner yabs.version_manager yabs.log yabs.util
   :parts: 2
   :caption: Standard Yabs Classes

Workflow Tasks
--------------

.. inheritance-diagram:: yabs.cmd_common yabs.cmd_bump yabs.cmd_check yabs.cmd_commit yabs.cmd_exec yabs.cmd_gh_release yabs.cmd_push yabs.cmd_pypi_release yabs.cmd_tag
   :parts: 2
   :caption: Workflow Tasks


Context Variables
=================
:class:`~yabs.task_runner.TaskContext`

inc (str)
    ...

repo (str)
    The GitHub repository name, e.g. *"mar10/wsgidav"*.
