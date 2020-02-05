.. _main-index:

########
stressor
########

*Stress-test your web app.*

:Project:   https://github.com/mar10/stressor/
:Version:   |version|, Date: |today|

|travis_badge| |nbsp| |pypi_badge| |nbsp| |lic_badge| |nbsp| |rtd_badge|

.. toctree::
   :hidden:

   Overview<self>
   installation
   user_guide.md
   reference_guide
   development
   changes


.. image:: stressor_48x48.png
   :height: 48px
   :width: 48px
   :alt: stressor

.. image:: ../../teaser.png
  :target: https://github.com/mar10/stressor
  :name: Live demo


.. warning::
  Stressor is currently Work In Progress and **not** fit for production!

..
  Major version updates (1.0 => 2.0, 2.0 => 3.0, ...) introduce
  *breaking changes* to the previous versions.
  Make sure to adjust your scripts accordingly after update.


Features
========

  * This is a command line tool...
  * ... and a library for use in custom Python projects.
  * TODO

**The command line tool adds:**

  * Runs on Linux, macOS, and Windows.
  * TODO


.. note:: Known Limitations

  * TODO


Quickstart
==========

Releases are hosted on `PyPI <https://pypi.python.org/pypi/stressor>`_ and can
be installed using `pipenv <https://github.com/kennethreitz/pipenv>`_ ::

  $ pipenv shell
  (stressor) $ pipenv install stressor --upgrade
  (stressor) $ stressor --help

(`Python 3.5+ <https://www.python.org/downloads/>`_ is required.)

..
  Indices and tables
  ==================

  * :ref:`genindex`
  * :ref:`modindex`
  * :ref:`search`


.. |travis_badge| image:: https://travis-ci.org/mar10/stressor.svg?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/mar10/stressor

.. |pypi_badge| image:: https://img.shields.io/pypi/v/stressor.svg
   :alt: PyPI Version
   :target: https://pypi.python.org/pypi/stressor/

.. |lic_badge| image:: https://img.shields.io/pypi/l/stressor.svg
   :alt: License
   :target: https://github.com/mar10/stressor/blob/master/LICENSE.txt

.. |rtd_badge| image:: https://readthedocs.org/projects/stressor/badge/?version=latest
   :target: https://stressor.readthedocs.io/
   :alt: Documentation Status

.. |logo| image:: stressor_48x48.png
   :height: 48px
   :width: 48px
   :alt: stressor

.. |stressor| raw:: html

   <a href="https://en.wikipedia.org/wiki/Stressor"><abbr title="A stressor is a chemical or biological agent, environmental condition, external stimulus or an event that causes stress to an organism.">stressor</abbr></a>
