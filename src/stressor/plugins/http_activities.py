# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re
import threading
from pprint import pformat
from queue import Empty, Queue
from urllib.parse import urlencode

from lxml import html
import requests
from requests.exceptions import RequestException

from stressor import __version__
from stressor.plugins.base import (
    ActivityAssertionError,
    ActivityBase,
    ActivityError,
    ActivityTimeoutError,
)
from stressor.util import (
    check_arg,
    get_dict_attr,
    logger,
    shorten_string,
    is_relative_url,
    resolve_url,
)


def match_value(pattern, value, info):
    """Return ."""
    check_arg(pattern, str)

    value = str(value)
    if "." in pattern or "*" in pattern:
        match = re.match(pattern, value)  # , re.MULTILINE)
    else:
        match = pattern == value

    if not match:
        msg = "`{}` value {!r} does not match pattern {!r}".format(info, value, pattern)
        return False, msg
    return True, None


class HTTPRequestActivity(ActivityBase):
    # RESPONSE_LOG_LENGTH = 200
    REQUEST_ARGS = {"auth", "data", "json", "headers", "params", "timeout", "verify"}
    _mandatory_args = {"method", "url"}
    _known_args = (
        REQUEST_ARGS
        | _mandatory_args
        | {
            "store_json",
            "assert_match_headers",
            "assert_status",
            "assert_json",
            "assert_html",
        }
    )

    _info_args = ("name", "method", "url")

    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, **activity_args)

        check_arg(activity_args.get("method"), str)
        check_arg(activity_args.get("url"), str)
        check_arg(activity_args.get("params"), dict, or_none=True)

        # self.r_args = {k: v for k, v in self.raw_args.items() if k in self.REQUEST_ARGS}
        # self.a_args = {
        #     k: v for k, v in self.raw_args.items() if k not in self.REQUEST_ARGS
        # }

    def get_info(self, info_args=True, expanded_args=None):
        args_dict = expanded_args if expanded_args else self.raw_args
        url = args_dict.get("url")
        params = args_dict.get("params") or ""

        if params:
            params = "?" + urlencode(params)
        if self.__class__ is HTTPRequestActivity:
            method = "{} ".format(args_dict["method"])
        else:
            method = ""
        return "{}({}{}{})".format(self.get_script_name(), method, url, params)

    @classmethod
    def _format_response(cls, resp, short=False, add_headers=False, ruler=True):

        try:
            s = resp.json()
            s = pformat(s)
        except ValueError:
            s = resp.text
            lines = []
            for s in s.split("\n"):
                s = s.rstrip()
                if s:
                    lines.append(s)
            s = "\n".join(lines)
            # s = fill(s)

        res = []
        res.append("")
        res.append(
            "--- Response status: {}, len: {:,} bytes: >>>".format(
                resp.status_code, len(resp.content)
            )
        )

        for k, v in resp.headers.items():
            res.append("{}: {}".format(k, v))
        res.append("- " * 20)

        if short:
            s = shorten_string(s, 500, 100, place_holder="\n[...]\n")
        res.append(s)
        res.append("<<< ---")
        return "\n".join(res)

    @classmethod
    def _raise_assertion(cls, cause, resp):
        msg = cls._format_response(resp, short=True)
        msg = "\n  | ".join(msg.split("\n"))
        raise ActivityAssertionError("{}\n{}".format(cause, msg))

    def execute(self, session, **expanded_args):
        """
        Raises:
            ActivityAssertionError:
            requests.exceptions.ConnectionError: 'Connection refused', etc.
            requests.exceptions.HTTPError: On 404, 500, etc.
        """
        url = expanded_args.get("url")
        base_url = session.get_context("base_url")
        if not base_url and is_relative_url(url):
            raise ActivityError(
                "Missing context variable 'base_url' to resolve relative URLs"
            )
        expanded_args.setdefault("timeout", session.get_context("timeout"))
        assert "timeout" in expanded_args
        debug = expanded_args.get("debug")

        # print("session.dry_run", session.dry_run)
        if session.dry_run:
            return expanded_args.get("mock_result", "dummy_result")

        bs = session.browser_session
        method = self.raw_args["method"]

        url = expanded_args.pop("url")
        url = resolve_url(base_url, url)

        r_args = {k: v for k, v in expanded_args.items() if k in self.REQUEST_ARGS}

        verify_ssl = session.sessions.get("verify_ssl", True)
        r_args.setdefault("verify", verify_ssl)

        basic_auth = session.sessions.get("basic_auth", False)
        if basic_auth:
            r_args.setdefault("auth", session.user.auth)

        headers = r_args.setdefault("headers", {})
        headers.setdefault(
            "User-Agent",
            "session/{} Stressor/{}".format(session.session_id, __version__),
        )

        # if debug:
        #     http_client.HTTPConnection.debuglevel = 1
        # else:
        #     http_client.HTTPConnection.debuglevel = 0
        if debug:
            logger.info("HTTPRequest({}, {}, {})...".format(method, url, r_args))

        # The actual HTTP request:
        try:
            resp = bs.request(method, url, **r_args)
        except requests.exceptions.Timeout as e:
            raise ActivityTimeoutError("{}".format(e))
        except RequestException as e:
            raise ActivityError("{}".format(e))

        is_json = False
        try:
            result = resp.json()
            is_json = True
        except ValueError:
            result = resp.text

        if not resp.ok:
            logger.error(self._format_response(resp, short=not debug))
        elif debug:
            logger.info(self._format_response(resp, short=False))

        assert_status = expanded_args.get("assert_status")
        if not assert_status:
            # requests.exceptions.HTTPError: On 404, 500, etc.
            resp.raise_for_status()
        elif resp.status_code not in assert_status:
            self._raise_assertion(
                "HTTP status does not match {}: {}".format(
                    assert_status, resp.status_code
                ),
                resp,
            )

        arg = expanded_args.get("assert_match_headers")
        if arg:
            text = str(resp.headers)
            if not re.match(arg, text):
                self._raise_assertion(
                    "Result headers do not match `{}`".format(arg), resp
                )

        arg = expanded_args.get("assert_json")
        if arg:
            if not is_json:
                self._raise_assertion("Unexpected result type (expected JSON)", resp)

            for key, pattern in arg.items():
                value = get_dict_attr(result, key)
                # print(result, key, value)
                match, msg = match_value(pattern, value, key)
                if not match:
                    self._raise_assertion("Unexpected JSON result {}".format(msg), resp)

        arg = expanded_args.get("assert_html")
        if arg:
            if is_json:
                self._raise_assertion("Unexpected result type (expected HTML)", resp)

            for xpath, pattern in arg.items():
                # print(result)
                tree = html.fromstring(result)
                # print("tree", html.tostring(tree))
                # match = tree.xpath("body/span[contains(@class, 'test') and text() = 'abc']")
                match = tree.xpath(xpath)
                if pattern is True:
                    ok = bool(match)
                elif pattern is False:
                    ok = not match
                elif not match:
                    ok = False
                else:
                    # print("match", html.tostring(match))
                    raise NotImplementedError
                if not ok:
                    self._raise_assertion(
                        "Unexpected HTML result: XPath {!r} -> {}".format(xpath, match),
                        resp,
                    )

        return result


class GetRequestActivity(HTTPRequestActivity):
    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, method="GET", **activity_args)


class PostRequestActivity(HTTPRequestActivity):
    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, method="POST", **activity_args)


class PutRequestActivity(HTTPRequestActivity):
    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, method="PUT", **activity_args)


class DeleteRequestActivity(HTTPRequestActivity):
    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, method="DELETE", **activity_args)


class StaticRequestsActivity(ActivityBase):
    REQUEST_ARGS = {"auth", "data", "json", "headers", "params", "timeout", "verify"}
    _mandatory_args = {"url_list"}
    _known_args = REQUEST_ARGS | _mandatory_args | {"assert_status", "thread_count"}
    _info_args = ("name", "method", "thread_count")
    """
    TODO: this activity recieves a list of URLs (JavaScript, Html, CSS, Images, ...)
    and loads them, using max. ~5 threads, as a browser would.
    """

    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, **activity_args)

    def execute(self, session, **expanded_args):
        """
        """
        url_list = expanded_args.pop("url_list")
        base_url = session.get_context("base_url")
        expanded_args.setdefault("timeout", session.get_context("timeout"))
        debug = expanded_args.get("debug")
        thread_count = int(expanded_args.get("thread_count", 1))
        method = "GET"
        r_args = {k: v for k, v in expanded_args.items() if k in self.REQUEST_ARGS}

        verify_ssl = session.sessions.get("verify_ssl", True)
        r_args.setdefault("verify", verify_ssl)

        basic_auth = session.sessions.get("basic_auth", False)
        if basic_auth:
            r_args.setdefault("auth", session.user.auth)

        headers = r_args.setdefault("headers", {})
        headers.setdefault(
            "User-Agent",
            "session/{} Stressor/{}".format(session.session_id, __version__),
        )

        # TODO: requests.Session is not guaranteed to be thread-safe!
        bs = session.browser_session
        # Queue-up all pending request
        queue = Queue()
        for url in url_list:
            url = resolve_url(base_url, url)
            queue.put(url)

        results = []

        def _work(name):
            # logger.debug("StaticRequests({}) started...".format(name, ))
            while not session.stop_request.is_set():
                try:
                    url = queue.get(False)
                except Empty:
                    break

                if debug:
                    logger.info("StaticRequests({}, {})...".format(name, url))
                # The actual HTTP request:
                # TODO: requests.Session is not guaranteed to be thread-safe!
                try:
                    res = bs.request(method, url, **r_args)
                    res.raise_for_status()
                    results.append((True, name, url, None))
                except Exception as e:
                    results.append((False, name, url, "{}".format(e)))
                queue.task_done()
            logger.debug("StaticRequests({}) stopped.".format(name))
            return

        logger.debug(
            "Starting {} StaticRequestsActivity workers...".format(thread_count)
        )

        thread_list = []
        for i in range(thread_count):
            name = "{}.{:02}".format(session.session_id, i + 1)
            t = threading.Thread(name=name, target=_work, args=[name])
            t.setDaemon(True)  # Required to make Ctrl-C work
            thread_list.append(t)

        for t in thread_list:
            t.start()

        logger.debug("All StaticRequestsActivity workers running...")
        queue.join()
        for t in thread_list:
            t.join()
        errors = ["{}".format(error) for ok, name, url, error in results if not ok]
        if errors:
            raise ActivityError(
                "{} reqests failed:\n{}".format(len(errors), format(errors))
            )
            # logger.error(pformat(errors))
        return bool(errors)


class PollRequestActivity(HTTPRequestActivity):
    """
    TODO: This activity simulates a peridodical request to a single URL.
    """

    def __init__(self, config_manager, **activity_args):
        raise NotImplementedError
        # TODO: honor force_single option
