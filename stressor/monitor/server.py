# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import socketserver
import os
import json
import io
import logging
from http.server import SimpleHTTPRequestHandler, HTTPStatus
from threading import Thread

from stressor import __version__

# from stressor.util import logger


logger = logging.getLogger("stressor.monitor")


class Handler(SimpleHTTPRequestHandler):
    server_version = (
        "stressor/" + __version__ + " " + SimpleHTTPRequestHandler.server_version
    )
    # Custom attributes, set by `Monitor`:
    DIRECTORY = None
    run_manager = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self.DIRECTORY, **kwargs)

    def log_request(self, code="-", size="-"):
        # Overide base implementation (writing to stderr)
        if isinstance(code, HTTPStatus) and not (200 <= code.value < 400):
            logger.warning('"%s" %s %s', self.requestline, str(code), str(size))
        else:
            logger.debug('"%s" %s %s', self.requestline, str(code), str(size))

    def log_error(self, format, *args):
        # Overide base implementation (writing to stderr)
        logger.error(format, *args)

    def log_message(self, format, *args):
        # Overide base implementation (writing to stderr)
        logger.debug(format, *args)

    def _return_json(self, body, status=HTTPStatus.OK):
        if not isinstance(body, str):
            body = json.dumps(body)
        encoded = body.encode("utf8", "surrogateescape")
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        # print(encoded)
        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        try:
            self.copyfile(f, self.wfile)
        finally:
            f.close()
        return f

    def on_stopManager(self, args):
        res = self.run_manager.stop()
        return self._return_json(res)

    def on_getStats(self, args):
        # res = {
        #     "stats": self.run_manager.get_status_info(),
        # }
        res = self.run_manager.get_status_info()
        return self._return_json(res)

    def do_GET(self):
        handler_name = self.path.strip("/")
        handler_name, _sep, args = handler_name.partition("?")
        handler = getattr(self, "on_" + handler_name, None)
        if callable(handler):
            try:
                return handler(args)
            except Exception as e:
                logger.exception(handler_name)
                return self._return_json(
                    {"fault": repr(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
                )

        return SimpleHTTPRequestHandler.do_GET(self)


class Monitor(Thread):
    """
    Run a web server in a separate thread, so it does not block
    """

    def __init__(self, run_manager, bind="", port=8081):
        super().__init__(name="stressor.monitor", daemon=None)
        Handler.DIRECTORY = os.path.join(os.path.dirname(__file__), "htdocs")
        Handler.run_manager = run_manager
        self.run_manager = run_manager
        self.bind = bind
        self.port = port
        self.httpd = None

    def run(self):
        with socketserver.TCPServer((self.bind, self.port), Handler) as httpd:
            self.httpd = httpd
            logger.info("Monitor serving at port {}:{}...".format(self.bind, self.port))
            httpd.serve_forever()
            self.httpd = None
            logger.info("Monitor server stopped.")

    def shutdown(self):
        if self.httpd:
            self.httpd.shutdown()
