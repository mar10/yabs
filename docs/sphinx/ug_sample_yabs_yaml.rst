=============
yabs.yaml
=============

The following file lists all available tasks with all available options and
respective defaults.

.. note::
    This is not a meaningful or realistic workflow definition, but rather
    a demonstration of what's available. |br|
    A realistic workflow would omit default options and execute tasks in a
    more useful order. |br|
    See :doc:`ug_writing_scripts` for an example.


Annotated Sample Configuration
------------------------------

.. literalinclude:: yabs_annotated.yaml
    :linenos:
    :language: yaml

.. The file must be named `.yabs.yaml` and located in the root folder of the
.. project. |br|
.. When :bash:`yabs run` is called, it looks for that file in the current
.. working directory and parent folders. |br|
.. When :bash:`yabs run` was called from a sub-folder, it has to be
.. clarified if the synchronization should be done for the whole project
.. (i.e. the root folder where `.yabs.yaml` is located), or only for the
.. current sub branch.
.. This can be done by passing the :bash:`--root` or :bash:`--here` option.

.. `.yabs.yaml` defines a list of *tasks* that have a name and a set of
.. options. |br|
.. Options are named like the command line arguments, using
.. `YAML <http://yaml.org/spec/1.2/spec.html>`_ syntax, e.g.
.. :bash:`--force` becomes :code:`force: true`
.. and :bash:`--delete-unmatched` becomes :code:`delete_unmatched: true`.

.. The :code:`command` and :code:`remote` options are mandarory. |br|
.. A :code:`local` option must *not* be specified, since the local target path
.. is implicitly set to the folder location of `.yabs.yaml`.

.. Task settings can be overidden by command line args, e.g.::

..     $ yabs run deploy_force --dry-run -v
..     $ yabs run --here

.. Example:

.. .. literalinclude:: ../yabs_annotated.yaml
..     :linenos:
..     :language: yaml


.. For a start, copy
.. :download:`Annotated Sample Configuration <../yabs_annotated.yaml>`,
.. rename it to `.yabs.yaml` (note the leading dot),
.. and edit it to your needs.
