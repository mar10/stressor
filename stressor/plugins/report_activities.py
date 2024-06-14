# -*- coding: utf-8 -*-
# (c) 2020-2023 Martin Wendt and contributors; see https://github.com/mar10/stressor
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import sqlite3
from abc import ABC, abstractmethod
from enum import IntEnum
from pathlib import Path
from typing import List, Literal

from stressor.plugins.base import ActivityBase, ActivityCompileError, ActivityError
from stressor.util import TContextPath, check_arg


class ScopeEnum(IntEnum):
    SCENARIO = 1
    SEQUENCE = 2
    ACTIVITY = 3


class ReportStatusEnum(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


TReportFormat = Literal["csv", "sqlite"]
TReportType = Literal["timing", "alert", "custom"]


class ReportTarget(ABC):
    formats = frozenset(["csv", "sqlite"])
    types = frozenset(["timing", "alert", "custom"])

    def __init__(self, type: TReportType, scenario_stamp: float) -> None:
        self.type: TReportType = type
        self.scenario_stamp: float = scenario_stamp

    @abstractmethod
    def connect_or_create(self): ...

    @abstractmethod
    def emit(self): ...

    def alert(self) -> None:
        pass


class SqliteReportTarget(ReportTarget):
    def __init__(
        self,
        type: TReportType,
        scenario_stamp: float,
        path: Path,
        table: str,
    ) -> None:
        super().__init__(type=type, scenario_stamp=scenario_stamp)
        self.path: Path = path
        self.table: str = table

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.type}, {self.path}#{self.table}>"

    def connect_or_create(self):
        sqlite3.connect(self.path)

    def emit(self) -> None:
        pass


class CSVReportTarget(ReportTarget):
    def __init__(
        self,
        type: TReportType,
        scenario_stamp: float,
        path: Path,
        extra_columns: List[str],
    ) -> None:
        super().__init__(type=type, scenario_stamp=scenario_stamp)
        self.path = path
        self.extra_columns = extra_columns

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.type}, {self.path}>"

    def connect_or_create(self):
        raise NotImplementedError

    def emit(self) -> None:
        pass


class ReportManager:
    """
    Manage a pool of :class:`ReportTarget` instances and provide methods
    to append report entries to CSV files or Sqlite databases.
    """

    def __init__(self, scenario_stamp: float) -> None:
        self.scenario_stamp = scenario_stamp
        self.targets = {}

    def flush(self):
        for t in self.targets.values():
            t.flush()

    def close(self):
        self.flush()
        for t in self.targets.values():
            t.close()
        self.targets = {}

    def add_target(
        self,
        *,
        type: TReportType,
        format: TReportFormat,
        path: Path,
        name: str = None,
        extra_columns: List = None,
    ) -> None:
        if type not in ReportTarget.types:
            raise ValueError(f"{type=}")

        if format == "csv":
            t = CSVReportTarget()
        elif format == "sqlite":
            if type in ("timing", "alert"):
                assert name is None
                name = type
            else:
                assert name

            t = SqliteReportTarget(
                type=self.type,
                scenario_stamp=self.scenario_stamp,
                path=path,
                table=name,
            )
        else:
            raise ValueError(f"{format=}")

        assert name not in self.targets, name
        self.targets[name] = t

    def emit_timing(
        self,
        *,
        stamp: float,
        scope: ScopeEnum,
        path: TContextPath,
        status: ReportStatusEnum = ReportStatusEnum.INFO,
        elap: float,
    ):
        pass

    def emit_alert(
        self,
        *,
        stamp: float,
        scope: ScopeEnum,
        path: TContextPath,
        status: ReportStatusEnum,
        message: str,
    ):
        pass

    def emit_custom(
        self,
        *,
        stamp: float,
        scope: ScopeEnum,
        path: TContextPath,
        status: ReportStatusEnum,
        extra_values: List,
    ):
        pass


# TODO: request sessions
class ReportActivity(ActivityBase):
    _mandatory_args = {"format", "path"}
    _known_args = {"columns", "tablename"}
    _info_args = ("name", "path")
    _default_ignore_timing = True  # not considerd for net timings

    def __init__(self, config_manager, **activity_args):
        """"""
        super().__init__(config_manager, **activity_args)

        path = Path(activity_args.get("path"))
        path = config_manager.resolve_path(path)

        format = activity_args.get("format")
        columns = activity_args.get("columns")
        tablename = activity_args.get("tablename")

        self.database = None
        if format == "csv":
            check_arg(columns, list, condition=columns)
        elif format == "sqlite":
            check_arg(tablename, str, condition=tablename)
            self.database = sqlite3.connect(path)
        else:
            raise ActivityCompileError(
                f"Unknown format {format!r}: expected 'csv' or 'sqlite'."
            )

        return

    def execute(self, session, **expanded_args):
        """"""

        raise ActivityError("Not implemented")

        # return result
