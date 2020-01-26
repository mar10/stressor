==========
User Guide
==========

.. toctree::
    :hidden:

    tutorial
    writing_scripts
    sample_pyftpsync_yaml


.. warning::
  Major version updates (1.0 => 2.0, 2.0 => 3.0, ...) introduce
  *breaking changes* to the previous versions.
  Make sure to adjust your scripts accordingly after update.


Command Line Interface
======================

Use the ``--help`` or ``-h`` argument to get help::

    $ stressor --help
    usage: stressor [-h] [-v | -q] [-V] {upload,download,sync,run,scan} ...

    Synchronize folders over FTP.

    positional arguments:
    {upload,download,sync,run,scan}
                            sub-command help
        upload              copy new and modified files to remote folder
        download            copy new and modified files from remote folder to
                            local target
        sync                synchronize new and modified files between remote
                            folder and local target
        run                 run stressor with configuration from
                            `.stressor.yaml` in current or parent folder
        scan                repair, purge, or check targets

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         increment verbosity by one (default: 3, range: 0..5)
    -q, --quiet           decrement verbosity by one
    -V, --version         show program's version number and exit

    See also https://github.com/mar10/stressor
    $


`run` command
-------------

In addition to the direct invocation of `upload`, `download`, or `sync`
commands, version 3.x allows to define a :doc:`sample_pyftpsync_yaml` file
in your project's root folder which then can be executed like so::

    $ stressor run

optionally, default settings can be overidden::

    $ stressor run --dry-run
    $ stressor run TASK

See the :doc:`sample_stressor_yaml` example for details.


Target URLs
-----------

The ``local`` and ``remote`` target arguments can be file paths or URLs
(currently the ``ftp:`` and ``ftps:`` protocols are supported)::

    $ stressor upload ~/temp ftp://example.com/target/folder

FTP URLs may contain credentials::

    $ stressor upload ~/temp ftp://joe:secret@example.com/target/folder

Note that `stressor` also supports prompting for passwords and storing
passwords
in the system keyring.


Verbosity Level
---------------

The verbosity level can have a value from 0 to 6:

=========  ======  ===========  =============================================
Verbosity  Option  Log level    Remarks
=========  ======  ===========  =============================================
  0        -qqq    CRITICAL     quiet
  1        -qq     ERROR        show errors only
  2        -q      WARN         show conflicts and 1 line summary only
  3                INFO         show write operations
  4        -v      DEBUG        show equal files
  5        -vv     DEBUG        diff-info and benchmark summary
  6        -vvv    DEBUG        show FTP commands
=========  ======  ===========  =============================================


Exit Codes
----------

The CLI returns those exit codes::

    0: OK
    1: Error (network, internal, ...)
    2: CLI syntax error
    3: Aborted by user

..    10: Unresolved conflicts remaining (with option --conflicts-as-error)


Script Examples
===============

All options that are available for command line, can also be passed to
the synchronizers. For example ``--delete-unmatched`` becomes
``"delete_unmatched": True``.

Upload modified files from local folder to FTP server::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FtpTarget
  from ftpsync.synchronizers import UploadSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FtpTarget("/temp", "example.com", username=user, password=passwd)
  opts = {"force": False, "delete_unmatched": True, "verbose": 3}
  s = UploadSynchronizer(local, remote, opts)
  s.run()

Synchronize a local folder with an FTP server using TLS::

  from ftpsync.targets import FsTarget
  from ftpsync.ftp_target import FtpTarget
  from ftpsync.synchronizers import BiDirSynchronizer

  local = FsTarget("~/temp")
  user ="joe"
  passwd = "secret"
  remote = FtpTarget("/temp", "example.com", username=user, password=passwd, tls=True)
  opts = {"resolve": "skip", "verbose": 1}
  s = BiDirSynchronizer(local, remote, opts)
  s.run()


Logging
-------

By default, the library initializes and uses a
`python logger <https://docs.python.org/library/logging.html>`_ named 'stressor'.
This logger can be customized like so::

    import logging

    logger = logging.getLogger("stressor")
    logger.setLevel(logging.DEBUG)

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
