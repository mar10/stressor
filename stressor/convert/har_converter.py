# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
https://w3c.github.io/web-performance/specs/HAR/Overview.html
"""
import json
import logging
import os
import re
from collections import Counter
from operator import itemgetter
from pprint import pformat
from urllib.parse import urlparse

from stressor.util import datetime_to_iso, iso_to_stamp, lstrip_string, shorten_string

logger = logging.getLogger("stressor.har")

EMPTY_TUPLE = tuple()


class HarConverter:
    """

    Example::

    """

    DEFAULT_OPTS = {
        "fspec": None,
        "target_folder": None,
        "force": False,
        "base_url": True,  # True: automatic
        "collate_statics_max": 10,
        # "add_req_comments": True,
        "skip_externals": True,
        "statics_types": (
            re.compile("image/.*", re.IGNORECASE),
            re.compile(".*/css", re.IGNORECASE),
            re.compile(".*/javascript", re.IGNORECASE),
            # "text/html",
        ),
        "skip_errors": True,
    }

    def __init__(self, opts):
        # self.stats = Counter()
        self.page_map = {}
        self.har_version = None
        self.browser_info = None
        self.creator_info = None
        self.first_entry_dt = None
        self.entries = []
        self.stats = Counter()
        self.prefix_counter = Counter()
        self.encoding = "utf-8-sig"
        self.opts = self.DEFAULT_OPTS.copy()
        self.opts.update(opts)
        #: (str) Available after `self._parse()`
        self.base_url = None
        self.polling_requests = []
        self.static_resources = []

    def run(self):
        har_path = self.opts.get("fspec")
        target_folder = self.opts.get("target_folder")

        if har_path is not None:
            har_path = os.path.abspath(har_path)
            if not os.path.isfile(har_path):
                raise FileNotFoundError(har_path)

            logger.info("Parsing {}...".format(har_path))
            self._parse(har_path)

            self._postprocess()

        if target_folder is None:
            assert har_path
            name = os.path.splitext(os.path.basename(har_path))[0].strip(".")
            target_folder = "./{}".format(name)
        target_folder = os.path.abspath(target_folder)
        if not os.path.isdir(target_folder):
            logger.info("Creating folder {}...".format(target_folder))
            os.mkdir(target_folder)

        self._init_from_templates(target_folder)

        if har_path is not None:
            fspec = os.path.join(target_folder, "main_sequence.yaml")
            self._write_sequence(fspec)
        return True

    def _copy_template(self, tmpl_name, target_path, kwargs):
        if not self.opts["force"] and os.path.isfile(target_path):
            raise RuntimeError(
                "File exists (use --force to continue): {}".format(target_path)
            )
            # raise FileExistsError(target_path)
        tmpl_folder = os.path.dirname(__file__)
        src_path = os.path.join(tmpl_folder, tmpl_name)
        tmpl = open(src_path, "rt", encoding=self.encoding).read()
        tmpl = tmpl.format(**kwargs)
        logger.info("Writing {:,} bytes to {!r}...".format(len(tmpl), target_path))
        with open(target_path, "w") as fp:
            fp.write(tmpl)
        # print(tmpl)
        return

    def _init_from_templates(self, target_folder):
        ctx = {
            "date": datetime_to_iso(),
            "name": "NAME",
            "tag": "TAG",
            "base_url": "URL",
            "details": "",
        }
        self._copy_template(
            "users.yaml.tmpl", os.path.join(target_folder, "users.yaml"), ctx
        )
        self._copy_template(
            "sequence.yaml.tmpl", os.path.join(target_folder, "main_sequence.yaml"), ctx
        )
        self._copy_template(
            "scenario.yaml.tmpl", os.path.join(target_folder, "scenario.yaml"), ctx
        )

    def _is_static(self, entry):
        mime_type = entry["resp_type"]
        for pattern in self.opts["statics_types"]:
            if pattern.match(mime_type):
                return True
        return False

    def _add_entry(self, har_entry):
        """Store the most important properties of an HAR entry."""
        req = har_entry["request"]
        resp = har_entry["response"]
        content = resp.get("content")

        # Record the usage count of the scheme+netloc, so we can pick the best
        # base_url later:
        url = req["url"]
        parse_result = urlparse(url)
        prefix = "{o.scheme}://{o.netloc}".format(o=parse_result)
        self.prefix_counter[prefix] += 1

        entry_dt = har_entry["startedDateTime"]
        if not self.first_entry_dt:
            self.first_entry_dt = entry_dt

        entry = {
            "start": iso_to_stamp(entry_dt),
            "method": req["method"],
            "url": url,
        }
        if req.get("httpVersion") not in ("", "HTTP/1.1"):
            logger.warning("Unknown httpVersion: {!r}".format(req.get("httpVersion")))
            # logger.warning("Unknown httpVersion: {}".format(req))

        if req.get("comment"):
            entry["comment"] = req["comment"]

        if req.get("queryString"):
            entry["query"] = req["queryString"]
        if req.get("postData"):
            entry["data"] = req["postData"]

        if resp.get("comment"):
            entry["resp_comment"] = resp["comment"]
        if content.get("mimeType"):
            entry["resp_type"] = content["mimeType"]
        if content.get("size"):
            entry["resp_size"] = content["size"]

        values = req.get("cookies")
        if values:
            cookies = entry["cookies"] = []
            for val in values:
                cookies.append((val["name"], val["value"]))

        values = req.get("headers")
        if values:
            headers = entry["headers"] = []
            for val in values:
                headers.append((val["name"], val["value"]))

        self.entries.append(entry)

    def _parse(self, fspec):
        with open(fspec, "r", encoding=self.encoding) as fp:
            har_data = json.load(fp)
        log = har_data["log"]
        assert len(har_data.keys()) == 1

        self.har_version = log["version"]

        creator = log["creator"]
        self.creator_info = "{}/{}".format(creator["name"], creator["version"])

        browser = log.get("browser")
        if browser:
            self.browser_info = "{}/{}".format(browser["name"], browser["version"])

        for page in log.get("pages", EMPTY_TUPLE):
            self.page_map[page["id"]] = page

        for entry in log["entries"]:
            self._add_entry(entry)

        # Sort entries
        # ("However the reader application should always make sure the array is sorted")
        self.entries.sort(key=itemgetter("start"))

        logger.debug("HAR:\n{}".format(pformat(self.entries)))
        # print("HAR:\n{}".format(pformat(self.entries)))
        return

    def _postprocess(self):
        # Figure out base_url
        base_url = self.opts.get("base_url")
        if base_url is True:
            # The most-used scheme+netloc is used as base_url
            # print(pformat(self.prefix_counter))
            base_url = self.prefix_counter.most_common(1)[0][0]
        self.base_url = base_url
        logger.info("Using base_url {!r}.".format(base_url))
        # print(base_url)

        # Remove unwanted entries and strip base_url where possible
        el = []
        skip_ext = self.opts["skip_externals"]
        for entry in self.entries:
            self.stats["entries_total"] += 1
            skip = False
            url = entry["url"]
            rel_url = lstrip_string(url, base_url, ignore_case=True)
            if rel_url is url:
                # The URL did not start with base_url, so it is 'external'
                if skip_ext:
                    logger.warning("Skipping external URL: {}".format(url))
                    self.stats["external_urls"] += 1
                    skip = True
            else:
                entry["url_org"] = url
                entry["url"] = rel_url

            if skip:
                self.stats["skipped"] += 1
            else:
                self.stats["entries"] += 1
                el.append(entry)

        self.entries = el
        return

    activity_map = {
        "GET": "GetRequest",
        "PUT": "PutRequest",
        "POST": "PostRequest",
        "DELETE": "DeleteRequest",
    }

    def _write_entry(self, fp, entry):

        activity = self.activity_map.get(entry["method"], "HTTPRequest")
        lines = []
        if entry.get("comment"):
            lines.append("# {}\n".format(shorten_string(entry["comment"], 75)))
        lines.append(
            "# Response type: {!r}, size: {:,}\n".format(
                entry.get("resp_type"), entry.get("resp_size", -1)
            )
        )
        if entry.get("resp_comment"):
            lines.append("# {}\n".format(shorten_string(entry["resp_comment"], 75)))

        url = entry["url"]

        lines.append("- activity: {}\n".format(activity))
        lines.append('  url: "{}"\n'.format(url))

        if activity == "HTTPRequest":
            lines.append("  method: {}\n".format(entry["method"]))
        # TODO:
        # We have ?query also as part of the URL
        # if entry.get("query"):
        #     lines.append("  params: {}\n".format(entry["query"]))
        if entry.get("data"):
            lines.append("  data: {}\n".format(entry["data"]))
        lines.append("\n")
        fp.writelines(lines)

    def _write_sequence(self, fspec):
        with open(fspec, "wt") as fp:
            fp.write("# Stressor Activity Definitions\n")
            fp.write("# Auto-generated {}\n".format(datetime_to_iso()))
            fp.write("# Source:\n")
            fp.write("#     File: {}\n".format(self.opts["fspec"]))
            fp.write("#     HAR Version: {}\n".format(self.har_version))
            fp.write("#     Creator: {}\n".format(self.creator_info))
            if self.browser_info:
                fp.write("#     Browser: {}\n".format(self.browser_info))
            fp.write("#     Recorded: {}\n".format(self.first_entry_dt))
            fp.write("#     Using base URL {!r}\n".format(self.base_url))
            fp.write("\n")

            for entry in self.entries:
                self._write_entry(fp, entry)
        return
