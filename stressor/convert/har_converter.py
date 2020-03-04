# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import json
import logging
import os
from pprint import pformat

from stressor.util import iso_datetime

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

    def run(self, fspec, target_folder):
        fspec = os.path.abspath(fspec)
        if not os.path.isfile(fspec):
            raise FileNotFoundError(fspec)
        if target_folder is None:
            target_folder = os.path.dirname(fspec)
        self._parse(fspec)
        self._init_from_templates(target_folder)
        self._write_sequence(target_folder)

    def _copy_template(self, tmpl_name, target_path, kwargs):
        tmpl_folder = os.path.dirname(__file__)
        src_path = os.path.join(tmpl_folder, tmpl_name)
        tmpl = open(src_path, "rt", encoding=self.encoding).read()
        tmpl = tmpl.format(**kwargs)
        logger.info("Writing {:,} bytes to {!r}...".format(len(tmpl), target_path))
        with open(target_path, "w") as fp:
            fp.write(tmpl)
        # print(tmpl)
        return

    def _init_from_templates(self, dest_folder):
        kwargs = {
            "date": iso_datetime(),
            "name": "NAME",
            "tag": "TAG",
            "base_url": "URL",
            "details": "",
        }
        self._copy_template(
            "users.yaml.tmpl", os.path.join(dest_folder, "users.yaml"), kwargs
        )
        self._copy_template(
            "scenario.yaml.tmpl", os.path.join(dest_folder, "scenario.yaml"), kwargs
        )

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

    def _parse(self, fspec):
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

        logger.info("HAR:\n{}".format(pformat(self.entries)))
        # print("HAR:\n{}".format(pformat(self.entries)))
        return

    activity_map = {
        "GET": "GetRequest",
        "PUT": "PutRequest",
        "POST": "PostRequest",
        "DELETE": "DeleteRequest",
    }

    def _write_entry(self, fp, entry):
        act = self.activity_map.get(entry["method"], "HTTPRequest")
        lines = [
            "- activity: {}\n".format(act),
            '  url: "{}"\n'.format(entry["url"]),
        ]
        fp.writelines(lines)

    def _write_sequence(self, dest_folder):
        fspec = os.path.join(dest_folder, "main_activities.yaml")
        with open(fspec, "wt") as fp:
            fp.write("# Stressor Activity Definitions\n")
            fp.write("# Auto-generated {}\n".format(iso_datetime()))
            for entry in self.entries:
                self._write_entry(fp, entry)
        return
