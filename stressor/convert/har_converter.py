# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import json
import logging
from pprint import pformat

# from stressor.util import format_elap, get_dict_attr, shorten_string

logger = logging.getLogger("stressor")

EMPTY_TUPLE = tuple()


class HarConverter:
    """

    Example::

    """

    def __init__(self):
        # self.stats = Counter()
        self.page_map = {}
        self.version = None
        self.info = None
        self.entries = []
        self.encoding = "utf-8-sig"

    def parse(self, fspec):
        with open(fspec, "r", encoding=self.encoding) as fp:
            har_data = json.load(fp)
        log = har_data["log"]
        assert len(har_data.keys()) == 1

        self.version = log["version"]

        creator = log["creator"]
        self.info = "{}/{}".format(creator["name"], creator["version"])

        for page in log.get("pages", EMPTY_TUPLE):
            self.page_map[page["id"]] = page

        for entry in log["entries"]:
            self._add_entry(entry)

        # logger.info("HAR:\n{}".format(pformat(self.entries)))
        print("HAR:\n{}".format(pformat(self.entries)))
        return

    def _add_entry(self, har_entry):
        req = har_entry["request"]
        entry = {
            "method": req["method"],
            "url": req["url"],
        }
        if req.get("httpVersion") != "HTTP/1.1":
            logger.debug("Unknown httpVersion: {}".format(req))

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
