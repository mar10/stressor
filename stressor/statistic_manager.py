# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import logging
from collections import defaultdict
from pprint import pformat

from stressor.util import check_arg, format_elap

logger = logging.getLogger("stressor")


class StatisticManager:
    def __init__(self, parent=None):
        check_arg(parent, StatisticManager, or_none=True)

        self.parent = parent
        self.timing_keys = set()
        self.stats = defaultdict(int)

    def __getitem__(self, key):
        return self.stats[key]

    def _make_key(self, key_or_activity):
        if isinstance(key_or_activity, str):
            return key_or_activity
        key = key_or_activity.compile_path
        return key

    def inc(self, key, ofs=1):
        key = self._make_key(key)
        self.stats[key] += ofs
        if self.parent:
            self.parent.inc(key, ofs)

    def add_timing(self, key, elap):
        key = self._make_key(key)
        self.timing_keys.add(key)
        count = self.stats[key + ".count"] + 1
        self.stats[key + ".count"] = count

        cum_time = self.stats[key + ".time"] + elap
        self.stats[key + ".time"] = cum_time

        if elap > self.stats[key + ".time_max"]:
            self.stats[key + ".time_max"] = elap
        self.stats[key + ".time_avg"] = cum_time / count

        if self.parent:
            self.parent.add_timing(key, elap)

    def add_error(self, key, error):
        key = self._make_key(key)
        self.stats[key + ".errors"] += 1
        self.stats[key + ".last_error"] = "{}".format(error)
        if self.parent:
            self.parent.add_error(key, error)

    def has_errors(self, or_warnings=False):
        error_count = self.stats["errors"]
        return error_count

    def format_result(self, simplify=True):
        s = dict(self.stats)
        if simplify:
            for k, v in list(s.items()):
                if k.endswith(".count") and v == 1:
                    kbase = k.rsplit(".", 1)[0]
                    s.pop(kbase + ".count", None)
                    s.pop(kbase + ".time_avg", None)
                    s.pop(kbase + ".time_max", None)
        return "{}".format(pformat(s))

    def format_result_ex(self):
        return "{}".format(pformat(dict(self.stats)))

    def get_monitor_info(self):
        stats = self.stats

        def f(key, secs=False):
            v = stats.get(key, 0)
            if secs:
                v = format_elap(v)
            # v = get_dict_attr(stats, key)
            return v

        # TODO: add rows for every sequence name:
        seq_stats = []
        seq_stats.append(
            [
                "Σ",
                f("activity.count"),
                f("errors"),
                f("session.time", True),
                f("session.time_max", True),
                f("session.time_avg", True),
                f("activity.time", True),
                f("activity.time_max", True),
                f("activity.time_avg", True),
            ]
        )
        # List of all activities that are marked `monitor: true`
        activity_stats = []
        for k in self.stats:
            if not k.startswith("/config") or not k.endswith(".count"):
                continue
            k = k.rsplit(".", 1)[0]
            activity_stats.append(
                [
                    k,
                    f(k + ".count"),
                    f(k + ".errors"),
                    f(k + ".time", True),
                    f(k + ".time_max", True),
                    f(k + ".time_avg", True),
                    f(k + ".last_error") or "n.a.",
                ]
            )

        res = {
            "hasErrors": self.has_errors(),
            "seq_stats": seq_stats,
            "act_stats": activity_stats,
            "raw": self.stats,
        }
        return res
