# -*- coding: utf-8 -*-
"""
(c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php

Test helpers.

Examples::

    with WsgiDavTestServer(opts):
       ... test methods

or for use in pytest, put this in ``conftest.py``::

    @pytest.fixture(scope="session")
    def mock_wsgidav_server_fixture():
        # Setup:
        htdocs_path = os.path.join(os.path.dirname(__file__), "fixtures/htdocs")
        test_server = WsgiDavTestServer(
            root=htdocs_path, auth=None, with_ssl=False, verbose=3
        )
        test_server.start()

        # Use:
        yield test_server

        # Teardown:
        test_server.stop()

then use it like this. This will start the server at most once throughout
the test whole session::

    class TestMyCode:
        def test_1(self, mock_wsgidav_server_fixture):
            ...

"""

import multiprocessing
import os
from tempfile import gettempdir

from wsgidav import util
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import WsgiDAVApp

DEFAULT_PORT = 8080


def run_wsgidav_server(root, auth, with_ssl, verbose=3, provider=None, **kwargs):
    """Start blocking WsgiDAV server (called as a separate process)."""

    package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    share_path = root
    if share_path is None:
        share_path = os.path.join(gettempdir(), "wsgidav-test")
        if not os.path.exists(share_path):
            os.mkdir(share_path)

    if provider is None:
        provider = FilesystemProvider(share_path)

    # config = DEFAULT_CONFIG.copy()
    # config.update({
    config = {
        "host": "127.0.0.1",
        "port": kwargs.get("port", DEFAULT_PORT),
        "provider_mapping": {"/": provider},
        # None: dc.simple_dc.SimpleDomainController(user_mapping)
        "http_authenticator": {"domain_controller": None},
        "simple_dc": {"user_mapping": {"*": True}},  # anonymous access
        "verbose": verbose,
        "enable_loggers": [],
        "property_manager": True,  # None: no property manager
        "lock_manager": True,  # True: use lock_manager.LockManager
    }

    if auth:
        username, password = auth
        config["http_authenticator"].update(
            {"accept_basic": True, "accept_digest": False, "default_to_digest": False}
        )
        config["simple_dc"].update(
            {
                "user_mapping": {
                    "*": {
                        username: {
                            "password": password,
                            "description": "",
                            "roles": [],
                        },
                        "tester": {
                            "password": "secret",
                            "description": "",
                            "roles": [],
                        },
                    }
                }
            }
        )

    if with_ssl:
        config.update(
            {
                "ssl_certificate": os.path.join(
                    package_path, "wsgidav/server/sample_bogo_server.crt"
                ),
                "ssl_private_key": os.path.join(
                    package_path, "wsgidav/server/sample_bogo_server.key"
                ),
                "ssl_certificate_chain": None,
                # "accept_digest": True,
                # "default_to_digest": True,
            }
        )

    # We want output captured for tests
    util.init_logging(config)

    # This event is .set() when server enters the request handler loop
    if kwargs.get("startup_event"):
        config["startup_event"] = kwargs["startup_event"]

    app = WsgiDAVApp(config)

    # from wsgidav.server.server_cli import _runBuiltIn
    # _runBuiltIn(app, config, None)
    from wsgidav.server.server_cli import _run_cheroot

    _run_cheroot(app, config, "cheroot")
    # blocking...


# ========================================================================
# WsgiDavTestServer
# ========================================================================


class WsgiDavTestServer:
    """Run a WsgiDAV at 127.0.0.1:8082 in a separate process."""

    def __init__(
        self,
        config=None,
        root=None,
        auth=None,
        with_ssl=False,
        verbose=3,
        port=DEFAULT_PORT,
        provider=None,
        profile=False,
    ):
        self.config = config
        self.root = root
        self.auth = auth
        self.with_ssl = with_ssl
        self.verbose = verbose
        self.port = port
        self.provider = provider
        if profile:
            raise NotImplementedError

        # self.start_delay = 2
        self.startup_event = multiprocessing.Event()
        self.startup_timeout = 5
        self.proc = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass

    def start(self):
        kwargs = {
            "root": self.root,
            "auth": self.auth,
            "with_ssl": self.with_ssl,
            "verbose": self.verbose,
            "port": self.port,
            "provider": self.provider,
            "startup_event": self.startup_event,
            "startup_timeout": self.startup_timeout,
        }
        print("Starting WsgiDavTestServer...: {}".format(kwargs))
        self.proc = multiprocessing.Process(target=run_wsgidav_server, kwargs=kwargs)
        self.proc.daemon = True
        self.proc.start()

        print("Starting WsgiDavTestServer... waiting for request loop...")

        if not self.startup_event.wait(self.startup_timeout):
            raise RuntimeError(
                "WsgiDavTestServer start() timed out after {} seconds".format(
                    self.startup_timeout
                )
            )
        print("Starting WsgiDavTestServer... running.")
        return self

    def stop(self):
        if self.proc:
            print("Stopping WsgiDAVAppTestServer...")
            self.proc.terminate()
            self.proc.join()
            self.proc = None
        print("Stopping WsgiDavTestServer... done.")
