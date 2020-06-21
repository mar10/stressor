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

from stressor.util import (
    base_url,
    datetime_to_iso,
    format_elap,
    is_yaml_keyword,
    iso_to_stamp,
    lstrip_string,
    shorten_string,
)

logger = logging.getLogger("stressor.har")

EMPTY_TUPLE = tuple()
PATTERN_TYPE = type(re.compile("foo"))  # 're.Pattern' requires Python 3.7+


class HarConverter:
    """Convert HAR file to YAML scenario."""

    #: Defaults for optional `--opts` paramter.
    DEFAULT_OPTS = {
        "fspec": None,
        "target_folder": None,
        "force": False,
        "base_url": True,  # True: automatic
        "collate_max_len": 100,  # put max 20 URL into one bucket
        "collate_max_duration": 1.0,  # a bucket spans max. 5 seconds
        "collate_max_pause": 0.2,  # 1 second gap will trigger open a new bucket
        "collate_thread_count": 5,
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
        pl = []
        for pattern in self.opts["statics_types"]:
            if isinstance(pattern, str):
                pattern = re.compile(pattern, re.IGNORECASE)
            assert isinstance(pattern, PATTERN_TYPE)
            pl.append(pattern)
        self.opts["statics_types"] = pl

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
            "base_url": self.base_url,
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

    _time_names = ("blocked", "dns", "connect", "send", "wait", "receive")

    def _calc_request_time(self, har_entry):
        t = 0.0
        timings = har_entry["timings"]
        for name in self._time_names:
            v = timings.get(name)
            if v > 0:
                t += v
        return t * 0.001

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
            "elap": self._calc_request_time(har_entry),
        }
        if req.get("httpVersion").upper() not in ("", "HTTP/1.1"):
            logger.warning("Unknown httpVersion: {!r}".format(req.get("httpVersion")))
            # logger.warning("Unknown httpVersion: {}".format(req))

        if req.get("comment"):
            entry["comment"] = req["comment"]

        if req.get("queryString"):  # List of (name, value) tuples
            entry["query"] = req["queryString"]

        if req.get("postData"):
            post_data = req["postData"]
            if post_data.get("mimeType"):
                entry["mimeType"] = post_data.get("mimeType")

            if post_data.get("params"):
                entry["data"] = post_data.get("params")
            elif post_data.get("text"):
                # according to spec, 'text' should be mutually exclusive to 'params'
                # but Chrome produces both or sometimes text only:
                entry["data"] = post_data.get("text")

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
        collate_max_len = self.opts["collate_max_len"]
        collate_max_duration = self.opts["collate_max_duration"]
        collate_max_pause = self.opts["collate_max_pause"]
        bucket = []
        bucket_start_stamp = 0
        bucket_last_stamp = 0

        def _flush():
            nonlocal bucket, bucket_start_stamp, bucket_last_stamp
            if not bucket:
                return
            self.stats["collated_activities"] += 1
            entry = bucket[0]
            entry["url_list"] = [e["url"] for e in bucket]
            # print("FLUSH\n{}".format(pformat(entry)))
            bucket = []
            bucket_start_stamp = 0
            bucket_last_stamp = 0

        for entry in self.entries:
            self.stats["entries_total"] += 1
            skip = False

            # Fix URL by removing the `base_url` prefix
            url = entry["url"]
            rel_url = lstrip_string(url, base_url, ignore_case=True)
            # The URL did not start with base_url, so it is 'external'
            is_external = rel_url is url
            if is_external:
                if skip_ext:
                    logger.warning("Skipping external URL: {}".format(url))
                    self.stats["external_urls"] += 1
                    skip = True
            else:
                entry["url_org"] = url
                entry["url"] = rel_url

            # Collate bursts of simple GET request to one single entry
            start = entry["start"]
            if len(bucket) >= collate_max_len:
                _flush()
            first = len(bucket) == 0

            if (
                collate_max_len > 1  # Collation enabled
                and entry["method"] == "GET"  # Only GET requests
                and not entry.get("data")  # No POST data
                and len(bucket) < collate_max_len  # Bucket size limit
                and (first or (start - bucket_start_stamp) <= collate_max_duration)
                and (first or (start - bucket_last_stamp) <= collate_max_pause)
                and self._is_static(entry)  # Only static resources (JS, CSS, ...)
            ):
                self.stats["collated_urls"] += 1
                bucket.append(entry)
                if not bucket_start_stamp:
                    bucket_start_stamp = start
                bucket_last_stamp = start
                # We keep the first entry, so we can add the bucket URLs there later
                if len(bucket) > 1:
                    skip = True
            elif bucket:
                # If a burst of simple requests is interrupted, flush and restart
                _flush()

            if skip:
                self.stats["skipped"] += 1
            else:
                self.stats["entries"] += 1
                el.append(entry)

        _flush()
        self.entries = el
        return

    activity_map = {
        "GET": "GetRequest",
        "PUT": "PutRequest",
        "POST": "PostRequest",
        "DELETE": "DeleteRequest",
    }

    def _write_args(self, lines, name, data):
        """
        Args:
            lines (list):
            name (str):
            data (list): a 'params' list of {name: ..., value: ...} objects
        """
        assert isinstance(data, (list, tuple))
        used = set()
        lines.append("  {}:\n".format(name))
        for p in data:
            # TODO: coerce value (which in HAR is always a string)

            # Convert [{name: ..., value: ...}, ...] syntax to dict
            # TODO: We do this, because activity code doesn not handle the
            #       tuple syntax yet. But we should fall back to tuples syntax
            #       if the list does contain duplicate names, instead of
            #       dicarding.
            name, value = p["name"], p["value"]
            # lines.append("    - ['{}', {}]\n".format(name, json.dumps(value)))

            if name in used:
                logger.error(
                    "Discarding multiple param name: {}: {}".format(name, value)
                )
                continue
            used.add(name)
            if not is_yaml_keyword(name):
                name = '"' + name + '"'
            lines.append("    {}: {}\n".format(name, json.dumps(value)))

        return

    def _write_entry(self, fp, entry):
        opts = self.opts
        activity = self.activity_map.get(entry["method"], "HTTPRequest")
        url_list = entry.get("url_list")
        is_bucket = bool(url_list) and len(url_list) > 1
        if is_bucket:
            activity = "StaticRequests"

        lines = []
        if entry.get("comment"):
            lines.append("# {}\n".format(shorten_string(entry["comment"], 75)))
        if is_bucket:
            lines.append("# Auto-collated {:,} GET requests\n".format(len(url_list)))
        else:
            lines.append(
                "# Response type: {!r}, size: {:,} bytes, time: {}\n".format(
                    entry.get("resp_type"),
                    entry.get("resp_size", -1),
                    format_elap(entry.get("elap"), high_prec=True),
                )
            )
        if entry.get("resp_comment"):
            lines.append("# {}\n".format(shorten_string(entry["resp_comment"], 75)))

        url = entry["url"]
        expand_url_params = False

        lines.append("- activity: {}\n".format(activity))
        if is_bucket:
            lines.append("  thread_count: {}\n".format(opts["collate_thread_count"]))
            lines.append("  url_list:\n")
            for url in url_list:
                lines.append("    - '{}'\n".format(url))
        else:
            if entry.get("query"):
                expand_url_params = True
                url = base_url(url)
            lines.append("  url: '{}'\n".format(url))

        if activity == "HTTPRequest":
            lines.append("  method: {}\n".format(entry["method"]))

        # TODO:
        # We have ?query also as part of the URL
        # if entry.get("query"):
        #     lines.append("  params: {}\n".format(entry["query"]))
        if expand_url_params:
            self._write_args(lines, "params", entry["query"])

        # TODO: set headers = {'Content-type': 'content_type_value'}
        #       if entry.dData.mimeType is defined

        data = entry.get("data")
        if data:
            if isinstance(data, (list, tuple)):
                # Must be a 'params' list of {name: ..., value: ...} objects
                self._write_args(lines, "data", data)
            else:
                assert type(data) is str
                logger.warning("Expected list, but got text: {!r}".format(data))
                lines.append("  data: {}\n".format(json.dumps(data)))

        lines.append("\n")
        fp.writelines(lines)

    def _write_sequence(self, fspec):
        logger.info("Writing activity sequence to {!r}...".format(fspec))
        with open(fspec, "wt") as fp:
            fp.write("# Stressor Activity Definitions\n")
            fp.write("# See https://stressor.readthedocs.io/\n")
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
        logger.info("Done.")
        return
