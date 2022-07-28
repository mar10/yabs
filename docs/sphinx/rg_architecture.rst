============
Architecture
============

..
    .. toctree::
    :hidden:


.. Overview
.. ========

.. Yabs is a tool, that runs a sequence of tasks om order to test, build, and
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

.. inheritance-diagram:: yabs.task_runner yabs.version_manager yabs.util
   :parts: 2
   :caption: Standard Yabs Classes

Workflow Tasks
--------------

.. inheritance-diagram:: yabs.task.common yabs.task.bump yabs.task.check yabs.task.commit yabs.task.exec yabs.task.github_release yabs.task.push yabs.task.pypi_release yabs.task.tag yabs.task.winget_release
   :parts: 3
   :caption: Workflow Tasks


Context Variables
=================
:class:`~yabs.task_runner.TaskContext`

inc (str)
    ...

repo (str)
    The GitHub repository name, e.g. *"mar10/wsgidav"*.
