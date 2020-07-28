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

from stressor.util import format_elap, format_rate, get_dict_attr, shorten_string

logger = logging.getLogger("stressor")


class StatisticManager:
    """

    Example::

        {'act_count': 4485,
        'act_time': 404.5604224205017,
        'act_time_avg': 0.09020299273589781,
        'act_time_max': 0.3416469097137451,
        'act_time_min': 0.00455021858215332,
        'errors': 0,
        'monitored': {'/config/sequences/main/2/activity': {'act_count': 889,
                                                            'act_time': 37.441248655319214,
                                                            'act_time_avg': 0.04211614021970665,
                                                            'act_time_max': 0.1545419692993164,
                                                            'act_time_min': 0.006118059158325195}},
        'net_act_count': 3586,
        'net_act_time': 132.06326842308044,
        'net_act_time_avg': 0.03682745912523158,
        'net_act_time_max': 0.1629331111907959,
        'net_act_time_min': 0.00455021858215332,
        'seq_count': 909,
        'seq_time': 405.6781575679779,
        'seq_time_avg': 0.4462906023850142,
        'seq_time_max': 0.6640150547027588,
        'seq_time_min': 0.04558515548706055,
        'sequence_stats': {'end': {'act_count': 20,
                                    'act_time': 1.2047512531280518,
                                    'act_time_avg': 0.060237562656402587,
                                    'act_time_max': 0.10723018646240234,
                                    'act_time_min': 0.0059051513671875,
                                    'errors': 0,
                                    'net_act_count': 10,
                                    'net_act_time': 0.17910146713256836,
                                    'net_act_time_avg': 0.017910146713256837,
                                    'net_act_time_max': 0.042352914810180664,
                                    'net_act_time_min': 0.0059051513671875,
                                    'seq_count': 10,
                                    'seq_time': 1.2114121913909912,
                                    'seq_time_avg': 0.12114121913909912,
                                    'seq_time_max': 0.14590692520141602,
                                    'seq_time_min': 0.1082160472869873,
                                    'warnings': 0},
                            'init': ...
        'sessions': {'t1': {'act_count': 454,
                            'act_time': 40.14628767967224,
                            'act_time_avg': 0.08842794643099612,
                            'act_time_max': 0.3342282772064209,
                            'act_time_min': 0.00455021858215332,
                            'errors': 0,
                            'net_act_count': 363,
                            'net_act_time': 12.54139757156372,
                            'net_act_time_avg': 0.034549304604858735,
                            'net_act_time_max': 0.11727690696716309,
                            'net_act_time_min': 0.00455021858215332,
                            'path': '/h1/p1/t1',
                            'seq_count': 92,
                            'seq_time': 40.26065945625305,
                            'seq_time_avg': 0.4376158636549245,
                            'seq_time_max': 0.6443750858306885,
                            'seq_time_min': 0.05200076103210449,
                            'user': 'User_1',
                            'warnings': 0},
                    't2': {'act_count': 449,
                    ...
        'stage': None,
        'warnings': 0}
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.stats = {
            "act_count": 0,
            "act_time": 0.0,
            "net_act_count": 0,
            "net_act_time": 0.0,
            "sess_count": 0,
            "sess_running": 0,
            "errors": 0,
            "warnings": 0,
            "run_limit_reached": False,
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
        res = {
            "name": name,
            "errors": 0,
            "warnings": 0,
        }
        self.stats["sequence_stats"][name] = res
        return res

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
            "active": False,
        }
        self.stats["sessions"][session.session_id] = d
        self.stats["sess_count"] += 1

    def _report(self, mode, session, sequence, activity, path=None, error=None):
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
                    sess_stats["path"] = path or activity.compile_path
                else:
                    # 'end' or 'error'
                    assert session.pending_activity is activity
                    elap = now - session.activity_start
                    session.pending_activity = None
                    session.activity_start = 0
                    # We add timings even if activity errored
                    is_net = not activity.ignore_timing

                    self._add_timing(global_stats, "act_", elap, is_net=is_net)
                    self._add_timing(sess_stats, "act_", elap, is_net=is_net)
                    self._add_timing(seq_stats, "act_", elap, is_net=is_net)

                    if activity.monitor:
                        d = global_stats["monitored"][key]
                        self._add_timing(d, "act_", elap, is_net=False)

                    if mode == "end":
                        pass
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
                    sess_stats["path"] = sequence
                else:
                    # 'end' or 'error'
                    assert session.pending_sequence == sequence
                    elap = now - session.sequence_start
                    session.pending_sequence = None
                    session.sequence_start = 0

                    self._add_timing(global_stats, "seq_", elap, is_net=False)
                    self._add_timing(seq_stats, "seq_", elap, is_net=False)
                    self._add_timing(sess_stats, "seq_", elap, is_net=False)
                    if mode == "end":
                        sess_stats["path"] = None
                    else:  # 'error'
                        self._add_error(seq_stats, error)

            elif session:
                if mode == "start":
                    global_stats["sess_running"] += 1
                else:
                    global_stats["sess_running"] -= 1
            else:
                if mode == "error":
                    global_stats["errors"] += 1

        return

    def report_start(self, session, sequence, activity, path=None):
        self._report("start", session, sequence, activity, path=path)

    def report_end(self, session, sequence, activity):
        self._report("end", session, sequence, activity)

    def report_error(self, session, sequence, activity, error):
        self._report("error", session, sequence, activity, error=error)

    def report_limit_violation(self, msg):
        """"Register 'limit reached' error (not more than once)."""
        if not self.stats["run_limit_reached"]:
            self.stats["run_limit_reached"] = True
            self.stats["errors"] += 1
            self.stats["last_error"] = msg

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
        d["last_error"] = shorten_string("{}".format(error), 500, 100)

    def error_count(self, or_warnings=False):
        error_count = self.stats["errors"]
        return error_count

    def has_errors(self, or_warnings=False):
        return self.error_count(or_warnings) > 0

    def format_result(self):
        s = dict(self.stats)
        return "{}".format(pformat(s))

    def get_monitor_info(self, config_all):
        stats = self.stats

        def f(d, k, secs=False):
            v = d.get(k, 0)
            if secs:
                v = format_elap(v)
            return v

        # --- Add rows for every sequence name:

        # Cache config_all.scenario.<sequence> entries as a dict:
        scenario_map = {}
        for scenario_seq_def in config_all["scenario"]:
            seq_name = scenario_seq_def["sequence"]
            scenario_map[seq_name] = scenario_seq_def

        seq_stats = []

        def _add_seq(name, info):
            title = name
            # Add duration/repeat info to the display title
            seq_def = scenario_map.get(name, {})
            extra = []
            if "repeat" in seq_def:
                extra.append("n: {:,}".format(seq_def["repeat"]))
            if "duration" in seq_def:
                extra.append("Δt: {}".format(format_elap(seq_def["duration"])))
            if extra:
                title = "{} ({})".format(seq_name, ", ".join(extra))

            seq_stats.append(
                {
                    "cols": [
                        title,
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
                        format_rate(
                            info.get("net_act_count"), info.get("net_act_time")
                        ),
                    ],
                    "type": "sequence",
                    "key": name if name != "Summary" else None,
                }
            )

        for seq_name in self.sequence_names:
            info = stats["sequence_stats"][seq_name]
            _add_seq(seq_name, info)
        _add_seq("Summary", stats)

        # --- List of all activities that are marked `monitor: true`
        activity_stats = []
        for act_compile_path in self.monitored_activities:
            info = stats["monitored"][act_compile_path]
            activity_stats.append(
                {
                    "cols": [
                        act_compile_path,
                        f(info, "act_count"),
                        f(info, "errors"),
                        f(info, "act_time", True),
                        f(info, "act_time_min", True),
                        f(info, "act_time_avg", True),
                        f(info, "act_time_max", True),
                        f(info, "last_error") or "n.a.",
                    ],
                    "type": "monitored",
                    "key": act_compile_path,
                }
            )

        # --- List all sessions
        sessions = []
        for idx, (session_id, info) in enumerate(stats["sessions"].items(), 1):
            sessions.append(
                {
                    "cols": [
                        idx,
                        session_id,
                        info["user"],
                        f(info, "seq_count"),
                        f(info, "act_count"),
                        f(info, "errors"),
                        info["path"],
                    ],
                    "type": "session",
                    "key": session_id,
                }
            )

        res = {
            "hasErrors": self.has_errors(),
            "seq_stats": seq_stats,
            "act_stats": activity_stats,
            "sess_stats": sessions,
            "raw": self.stats,
        }
        return res

    def get_error_info(self, args):
        type_ = args["type"]
        key = args["key"]
        if type_ == "sequence":
            errors = self.stats["sequence_stats"][key]["last_error"]
        elif type_ == "session":
            errors = self.stats["sessions"][key]["last_error"]
        elif type_ == "monitored":
            errors = self.stats["monitored"][key]["last_error"]

        return "Last Error Info ({}):\n\n{}".format(args, errors)
