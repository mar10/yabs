---------------
Writing Plugins
---------------

.. warning::

    The plugin API is still preliminary: expect changeges!

Additional task types can be added to *Yabs* by the way of *plugins*.

For example let's assume we need a new task `cowsay` that is used like so:

.. code-block:: yaml

    - task: cowsay
      message: |
        Dear fellow cattle,
        We just released version {version}.
        (This message was brought to you by the 'yabs-cowsay' extension.)

and produces this output:

.. code-block:: bash

     _________________________________________
    / Dear fellow cattle,                     \
    | We just released version 0.0.19-a2.     |
    | (This message was brought to you by the |
    \ 'yabs-cowsay' extension.)               /
     -----------------------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||


See the `sample implementation <https://github.com/mar10/yabs-cowsay>`_
for details.

.. note::

    Please let's reserve the namespace ``yabs-TASKNAME`` for 'official'
    extensions. |br|
    If you publish your own custom extension on PyPI, choose a name like
    ``yabs-USER-TASKNAME`` or similar.

    Also add 'yabs-plugin' to the keywords and ``Framework :: Yabs`` to the
    classifiers.
