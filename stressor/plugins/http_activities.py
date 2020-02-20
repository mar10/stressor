# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re
from pprint import pformat
from urllib.parse import urlencode, urljoin

# import http.client as http_client
from lxml import html

from stressor import __version__
from stressor.plugins.base import ActivityAssertionError, ActivityBase, ActivityError
from stressor.util import check_arg, get_dict_attr, logger, shorten_string


def is_abs_url(url):
    """Return true if url is already absolute."""
    return "://" in url or url.startswith("/")


def resolve_url(root, url):
    """Convert relaative URL to absolute, using `root` as default."""
    return urljoin(root, url)


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
    REQUEST_ARGS = frozenset(
        ("auth", "data", "json", "headers", "params", "timeout", "verify")
    )
    # ACTIVITY_ARGS = frozenset(
    #     (
    #         "assert_match",
    #         "assert_match_headers",
    #         "assert_max_time",
    #         "assert_status",
    #         "debug",
    #         "mock_result",
    #         "store_json",
    #     )
    # )

    def __init__(self, config_manager, **activity_args):
        super().__init__(config_manager, **activity_args)

        check_arg(activity_args.get("method"), str)
        check_arg(activity_args.get("url"), str)
        check_arg(activity_args.get("params"), dict, or_none=True)

        # self.r_args = {k: v for k, v in self.raw_args.items() if k in self.REQUEST_ARGS}
        # self.a_args = {
        #     k: v for k, v in self.raw_args.items() if k not in self.REQUEST_ARGS
        # }

    def __str__(self):
        url = self.raw_args.get("url")
        params = self.raw_args.get("params") or ""
        if params:
            params = "?" + urlencode(params)
        if self.__class__ is HTTPRequestActivity:
            method = "{} ".format(self.raw_args["method"])
        else:
            method = ""
        return "{}({}{}{})".format(self.get_script_name(), method, url, params)

    def _format_response(self, resp, short=False, add_headers=False, ruler=True):
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

    def execute(self, session, **expanded_args):
        """
        Raises:
            ActivityAssertionError:
            requests.exceptions.ConnectionError: 'Connection refused', etc.
            requests.exceptions.HTTPError: On 404, 500, etc.
        """
        url = expanded_args.get("url")
        base_url = session.get_context("base_url")
        if not base_url and not is_abs_url(url):
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
        resp = bs.request(method, url, **r_args)

        is_json = False
        try:
            result = resp.json()
            is_json = True
        except ValueError:
            result = resp.text

        if not resp.ok:
            s = self._format_response(resp, short=True)
            logger.error(s)

        if debug:
            # not only with --verbose?
            logger.info(self._format_response(resp, short=False))
            # logger.debug(self._format_response(resp, short=False))

        assert_status = expanded_args.get("assert_status")
        if not assert_status:
            # requests.exceptions.HTTPError: On 404, 500, etc.
            resp.raise_for_status()
        elif resp.status_code not in assert_status:
            raise ActivityAssertionError(
                "HTTP status does not match {}: {}".format(
                    assert_status, resp.status_code
                )
            )

        arg = expanded_args.get("assert_match_headers")
        if arg:
            text = str(resp.headers)
            if not re.match(arg, text):
                raise ActivityAssertionError(
                    "Result headers do not match `{}`: {!r}".format(
                        arg, shorten_string(text, 200)
                    )
                )

        arg = expanded_args.get("assert_json")
        if arg:
            if not is_json:
                raise ActivityAssertionError(
                    "Unexpected result type (expected JSON): {}".format(
                        shorten_string(result, 200)
                    )
                )
            for key, pattern in arg.items():
                value = get_dict_attr(result, key)
                # print(result, key, value)
                match, msg = match_value(pattern, value, key)
                if not match:
                    raise ActivityAssertionError(
                        "Unexpected JSON result: {}".format(msg)
                    )

        arg = expanded_args.get("assert_html")
        if arg:
            if is_json:
                raise ActivityAssertionError(
                    "Unexpected result type (expected HTML): {}".format(
                        shorten_string(result, 200)
                    )
                )
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
                    raise ActivityAssertionError(
                        "Unexpected HTML result: XPath {!r} -> {}".format(xpath, match)
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


class StaticRequestActivity(HTTPRequestActivity):
    """
    TODO: this activity recieves a list of URLs (JavaScrip, Html, CSS, Images, ...)
    and load them, using max. ~5 threads, as a Broweer would.
    """

    def __init__(self, config_manager, **activity_args):
        raise NotImplementedError


class PollRequestActivity(HTTPRequestActivity):
    """
    TODO: This activity simulates a peridodical request to a single URL.
    """

    def __init__(self, config_manager, **activity_args):
        raise NotImplementedError
        # TODO: honor force_single option
