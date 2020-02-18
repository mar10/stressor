# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import logging
import threading
import time
from collections import OrderedDict
from pprint import pformat

from stressor.util import format_elap, get_dict_attr, shorten_string

logger = logging.getLogger("stressor")


class StatisticManager:
    def __init__(self):
        self._lock = threading.RLock()
        self.stats = {
            "act_count": 0,
            "act_time": 0.0,
            "net_act_count": 0,
            "net_act_time": 0.0,
            "errors": 0,
            "warnings": 0,
            "stage": None,
            "sequence_stats": {},
            "sessions": {},
            "monitored": {},
        }
        self.sequence_names = OrderedDict()
        self.monitored_activities = OrderedDict()

    def __getitem__(self, key):
        return get_dict_attr(self.stats, key)

    def register_sequence(self, name):
        """Called by compiler."""
        assert name not in self.sequence_names
        self.sequence_names[name] = True
        self.stats["sequence_stats"][name] = {
            "errors": 0,
            "warnings": 0,
        }

    def register_activity(self, activity):
        """Called by compiler."""
        name = activity.compile_path
        assert name not in self.monitored_activities
        if activity.raw_args.get("monitor"):
            self.monitored_activities[name] = True
            self.stats["monitored"][name] = {}
        return

    def register_session(self, session):
        """Called by run_manager."""
        d = {
            "errors": 0,
            "warnings": 0,
            "user": session.user.name,
            "path": str(session.context_stack),
        }
        self.stats["sessions"][session.session_id] = d

    """
    Stats:
        activities: int
        net_activities: int
        sequences: int
        errors: int
        warnings: int
        started: stamp
        ended: stamp
        time: float
        net_time: float
        last_error: str
        last_warning: str
        stage: str
        sessions:
            sid1:
                activities: int
                net_activities: int
                sequences: int
                errors: int
                warnings: int
                started: stamp
                ended: stamp
                time: float
                net_time: float
                activities_per_sec_60: float
                activities_per_sec_300: float
                errors_per_sec_60: float
                errors_per_sec_300: float
                cur_activity: str
                last_error: str
                last_warning: str
                stage: str
            sid2:
                ...
        sequence_stats:
            seq_1:
                activities: int
                net_activities: int
                count: int
                errors: int
                warnings: int
                time: float
                time_avg: float
                time_min: float
                time_max: float
                net_time: float
                net_time_avg: float
                net_time_min: float
                net_time_max: float
                activities_per_sec_60: float
                activities_per_sec_300: float
                errors_per_sec_60: float
                errors_per_sec_300: float
                last_error: str
                last_warning: str
            seq_2:
                ...
        monitored:
            act_path_1:
                count: int
                errors: int
                warnings: int
                time: float
                time_avg: float
                time_min: float
                time_max: float
                last_error: str
                last_warning: str
            act_path_2:
                ...
    Snapshot:
        activities: int
        sessions: int
        sessions_active: int
        sessions_done: int
        errors: int
        warnings: int
        activities_per_sec_60: float
        activities_per_sec_300: float
        errors_per_sec_60: float
        errors_per_sec_300: float
    """

    def _report(self, mode, session, sequence, activity, error=None):
        assert mode in ("start", "end", "error")
        assert mode == "error" or error is None

        # print("*** _report", mode, session, sequence, activity, error)

        global_stats = self.stats
        sess_stats = global_stats["sessions"][session.session_id] if session else None
        seq_stats = global_stats["sequence_stats"][sequence] if sequence else None

        elap = 0

        with self._lock:
            now = time.time()
            if activity:
                assert session and sequence
                key = activity.compile_path
                if mode == "start":
                    assert session.pending_activity is None
                    session.pending_activity = activity
                    session.activity_start = now
                else:
                    # 'end' or 'error'
                    assert session.pending_activity is activity
                    elap = now - session.activity_start
                    session.pending_activity = None
                    session.activity_start = 0
                    if mode == "end":
                        is_net = not activity.ignore_timing

                        self._add_timing(global_stats, "act_", elap, is_net=is_net)
                        self._add_timing(sess_stats, "act_", elap, is_net=is_net)
                        self._add_timing(seq_stats, "act_", elap, is_net=is_net)

                        if activity.monitor:
                            d = global_stats["monitored"][key]
                            self._add_timing(d, "act_", elap, is_net=False)
                    else:  # 'error'
                        self._add_error(global_stats, error)
                        self._add_error(sess_stats, error)
                        self._add_error(seq_stats, error)
                        if activity.monitor:
                            d = global_stats["monitored"][key]
                            self._add_error(d, error)

            elif sequence:
                assert session
                if mode == "start":
                    assert session.pending_sequence is None
                    session.pending_sequence = sequence
                    session.sequence_start = now
                else:
                    # 'end' or 'error'
                    assert session.pending_sequence == sequence
                    elap = now - session.sequence_start
                    session.pending_sequence = None
                    session.sequence_start = 0
                    if mode == "end":
                        self._add_timing(global_stats, "seq_", elap, is_net=False)
                        self._add_timing(seq_stats, "seq_", elap, is_net=False)
                        self._add_timing(sess_stats, "seq_", elap, is_net=False)
                    else:  # 'error'
                        self._add_error(seq_stats, error)

            elif session:
                if mode == "start":
                    pass
                else:
                    pass
            else:
                if mode == "error":
                    global_stats["errors"] += 1

        return

    def report_start(self, session, sequence, activity):
        self._report("start", session, sequence, activity)

    def report_end(self, session, sequence, activity):
        self._report("end", session, sequence, activity)

    def report_error(self, session, sequence, activity, error):
        self._report("error", session, sequence, activity, error)

    def _add_timing(self, d, key_prefix, elap, is_net=None):
        p = key_prefix
        count = d.setdefault(p + "count", 0) + 1
        time_tot = d.setdefault(p + "time", 0.0) + elap
        time_max = d.setdefault(p + "time_max", 0.0)
        time_min = d.setdefault(p + "time_min", 0.0)

        d[p + "count"] = count
        d[p + "time"] = time_tot
        if elap > time_max:
            d[p + "time_max"] = elap
        if time_min == 0.0 or elap < time_min:
            d[p + "time_min"] = elap
        d[p + "time_avg"] = time_tot / count

        if is_net:
            p = "net_" + key_prefix
            self._add_timing(d, p, elap)
        return

    def _add_error(self, d, error):
        d.setdefault("errors", 0)
        d["errors"] += 1
        d["last_error"] = shorten_string("{}".format(error), 50)

    def has_errors(self, or_warnings=False):
        error_count = self.stats["errors"]
        return error_count > 0

    def format_result(self):
        s = dict(self.stats)
        return "{}".format(pformat(s))

    def get_monitor_info(self):
        stats = self.stats

        def f(d, k, secs=False):
            v = d.get(k, 0)
            if secs:
                v = format_elap(v)
            return v

        # Add rows for every sequence name:
        seq_stats = []

        def _add_seq(name, info):
            seq_stats.append(
                [
                    name,
                    f(info, "seq_count"),
                    f(info, "seq_time", True),
                    f(info, "seq_time_avg", True),
                    f(info, "seq_time_max", True),
                    f(info, "act_count"),
                    f(info, "errors"),
                    f(info, "net_act_count"),
                    f(info, "net_act_time", True),
                    f(info, "net_act_time_avg", True),
                    f(info, "net_act_time_max", True),
                ]
            )

        for seq_name in self.sequence_names:
            info = stats["sequence_stats"][seq_name]
            _add_seq(seq_name, info)
        _add_seq("Summary", stats)

        # List of all activities that are marked `monitor: true`
        activity_stats = []
        for act_compile_path in self.monitored_activities:
            info = stats["monitored"][act_compile_path]
            activity_stats.append(
                [
                    act_compile_path,
                    f(info, "act_count"),
                    f(info, "errors"),
                    f(info, "act_time", True),
                    f(info, "act_time_min", True),
                    f(info, "act_time_avg", True),
                    f(info, "act_time_max", True),
                    f(info, "last_error") or "n.a.",
                ]
            )

        # Sessions
        sessions = []
        for idx, (session_id, info) in enumerate(stats["sessions"].items(), 1):
            sessions.append(
                [
                    idx,
                    session_id,
                    info["user"],
                    f(info, "sequences"),
                    f(info, "activities"),
                    f(info, "errors"),
                    info["path"],
                ]
            )

        res = {
            "hasErrors": self.has_errors(),
            "seq_stats": seq_stats,
            "act_stats": activity_stats,
            "sess_stats": sessions,
            "raw": self.stats,
        }
        return res
