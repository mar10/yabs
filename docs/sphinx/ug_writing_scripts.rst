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


Script Activities
-----------------

`RunScript` activities are the swiss army knife for the scenario definitions.
The follwing example shows inline script definitions.

.. code-block:: yaml
    :linenos:

    main:

    - activity: RunScript
        export: ["the_answer"]
        script: |
        the_answer = 6 * 7
        print("The answer is {}".format(the_answer))

    - activity: RunScript
        name: "GET example.com"
        # debug: true
        script: |
        r = session.browser.get("http://example.com")
        result = r.status_code


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
