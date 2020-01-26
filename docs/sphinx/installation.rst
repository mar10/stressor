Installation
============

Requirements: `Python <https://www.python.org/downloads/>`_ 3.5+ is required.
Releases are hosted on `PyPI <https://pypi.python.org/pypi/stressor>`_ and can
be installed using
`pip <https://pip.pypa.io/en/stable>`_
or `pipenv <https://github.com/kennethreitz/pipenv>`_.

Install Into the System Python
------------------------------

Installing `stressor` as part of your system's Python will make the |CLI|
available from the command line.
You may need administrator permissions, like ``sudo``.
Also make sure to use Python 3 if the system installation uses Python 2
(as on macOS).

For example::

  $ sudo python3 -m pip install -U stressor
  $ stressor --version -v
  stressor/2.0.1 Python/3.6.1 Darwin-17.6.0-x86_64-i386-64bit
  $ stressor --help
  ...

Run From a Virtual Environment
------------------------------

Installing `stressor` and its dependencies into a 'sandbox' will help to keep
your system Python clean, but requires to activate the virtual environment::

  $ cd /path/to/stressor
  $ pipenv shell
  (stressor) $ pipenv install stressor --upgrade
  (stressor) $ stressor --version -v
  stressor/0.0.1 Python/3.6.1 Darwin-17.6.0-x86_64-i386-64bit
  (stressor) $ stressor --help
  ...

.. note::
   MS Windows users that only need the command line interface may prefer the
   `MSI installer <https://github.com/mar10/stressor/releases>`_.

.. seealso::
   See :doc:`development` for directions for contributors.

Now the ``stressor`` command is available::

  $ stressor --help

and the ``stressor`` package can be used in Python code::

  $ python
  >>> from stressor import __version__
  >>> __version__
  '0.0.1'
