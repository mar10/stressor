# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os
from test.mock_server import WsgiDavTestServer

import pytest


@pytest.fixture(scope="session")
def mock_wsgidav_server_fixture():
    """
    See comment in mock_server.py
    """
    # Setup:
    htdocs_path = os.path.join(os.path.dirname(__file__), "fixtures/htdocs")
    test_server = WsgiDavTestServer(
        root=htdocs_path, auth=None, with_ssl=False, verbose=3, port=8082
    )
    test_server.start()

    # Use:
    yield

    # Teardown:
    test_server.stop()
    # assert 0
