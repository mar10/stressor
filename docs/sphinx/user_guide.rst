==========
User Guide
==========

.. toctree::
    :hidden:

    tutorial
    writing_scripts
    sample_pyftpsync_yaml


.. warning::
  Stressor is currently Work In Progress and **not** fit for production!

..
  Major version updates (1.0 => 2.0, 2.0 => 3.0, ...) introduce
  *breaking changes* to the previous versions.
  Make sure to adjust your scripts accordingly after update.


Command Line Interface
======================

Use the ``--help`` or ``-h`` argument to get help::

    $ stressor --help
    usage: stressor [-h] [-v | -q] [-V] {run} ...

    Stress-test your web app.

    positional arguments:
    {run}          sub-command help
        run          run a test suite scenario

    optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet    decrement verbosity by one
    -V, --version  display versin info and exit (combine with -v for more
                    information)

    See also https://github.com/mar10/stressor
    $


`run` command
-------------

The main purpose of the stressor command line tool is to execute a test
scenario::

    $ stressor run my_scenario_config.yaml --monitor

See also the help::

    $ stressor run --help
    usage: stressor run [-h] [-v | -q] [-n] [-o [OPTION [OPTION ...]]] [--single]
                        [--monitor]
                        PROJECT

    positional arguments:
    PROJECT               path to configuration file (default: ./project.yaml)

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet           decrement verbosity by one
    -n, --dry-run         just simulate and log results, but don't change
                            anything
    -o [OPTION [OPTION ...]], --option [OPTION [OPTION ...]]
                            override configuration, syntax `OPTION:VALUE`
                            (multiple values allowed)
    --single              Force `run_config.sessions.count: 1`, so only one
                            thread is run
    --monitor             Open a web server and browser application to display
                            real-time progress
    $

See the :doc:`sample_stressor_yaml` example for details.



Verbosity Level
---------------

The verbosity level can have a value from 0 to 6:

=========  ======  ===========  =============================================
Verbosity  Option  Log level    Remarks
=========  ======  ===========  =============================================
  0        -qqq    CRITICAL     quiet
  1        -qq     ERROR
  2        -q      WARN         show less info
  3                INFO         show write operations
  4        -v      DEBUG        show more info
  5        -vv     DEBUG
  6        -vvv    DEBUG
=========  ======  ===========  =============================================


Exit Codes
----------

The CLI returns those exit codes::

    0: OK
    1: Error (network, internal, ...)
    2: CLI syntax error
    3: Aborted by user


..

    Script Examples
    ===============

    .. All options that are available for command line, can also be passed to
    .. the synchronizers. For example ``--delete-unmatched`` becomes
    .. ``"delete_unmatched": True``.

    .. Upload modified files from local folder to FTP server::

    .. from ftpsync.targets import FsTarget
    .. from ftpsync.ftp_target import FtpTarget
    .. from ftpsync.synchronizers import UploadSynchronizer

    .. local = FsTarget("~/temp")
    .. user ="joe"
    .. passwd = "secret"
    .. remote = FtpTarget("/temp", "example.com", username=user, password=passwd)
    .. opts = {"force": False, "delete_unmatched": True, "verbose": 3}
    .. s = UploadSynchronizer(local, remote, opts)
    .. s.run()

    .. Synchronize a local folder with an FTP server using TLS::

    .. from ftpsync.targets import FsTarget
    .. from ftpsync.ftp_target import FtpTarget
    .. from ftpsync.synchronizers import BiDirSynchronizer

    .. local = FsTarget("~/temp")
    .. user ="joe"
    .. passwd = "secret"
    .. remote = FtpTarget("/temp", "example.com", username=user, password=passwd, tls=True)
    .. opts = {"resolve": "skip", "verbose": 1}
    .. s = BiDirSynchronizer(local, remote, opts)
    .. s.run()


Logging
-------

By default, the library initializes and uses a
`python logger <https://docs.python.org/library/logging.html>`_ named 'stressor'.
This logger can be customized like so::

    import logging

    logger = logging.getLogger("stressor")
    logger.setLevel(logging.DEBUG)

..
    and replaced like so::

        import logging
        import logging.handlers
        from ftpsync.util import set_pyftpsync_logger

        custom_logger = logging.getLogger("my.logger")
        log_path = "/my/path/stressor.log"
        handler = logging.handlers.WatchedFileHandler(log_path)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        custom_logger.addHandler(handler)

        set_pyftpsync_logger(custom_logger)


    .. note::

        The CLI calls ``set_pyftpsync_logger(None)`` on startup, so it logs to stdout
        (and stderr).
