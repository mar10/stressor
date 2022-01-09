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

Clone stressor to a local folder and checkout the branch you want to work on::

    $ git clone git@github.com:mar10/stressor.git
    $ cd stressor
    $ git checkout my_branch


Work in a Virtual Environment
-----------------------------

Install Python
^^^^^^^^^^^^^^
We need `Python 3.5+ <https://www.python.org/downloads/>`_,
and `pipenv <https://github.com/kennethreitz/pipenv>`_ on our system.

If you want to run tests on *all* supported platforms, install Python 3.5,
3.6, 3.7, and 3.8.

Create and Activate the Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install dependencies for debugging::

    $ cd /path/to/stressor
    $ pipenv shell
    (stressor) $ pipenv install --dev
    (stressor) $

The development requirements already contain the stressor source folder, so
``pipenv install -e .`` is not required.

The code should now run::

    $ stressor --version
    2.0.0

The test suite should run as well::

    $ tox

Build Sphinx documentation to target: `<stressor>/docs/sphinx-build/index.html`) ::

    $ tox -e docs


Run Tests
=========

Run all tests with coverage report. Results are written to <stressor>/htmlcov/index.html::

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
        `travis <https://app.travis-ci.com/github/mar10/stressor>`_,
        so run ``$ tox`` and ``$ tox -e format`` frequently and before
        you commit!


Create a Pull Request
=====================

.. todo::

    	TODO
