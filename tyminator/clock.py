# Copyright 2023-2025 The Milton Hirsch Institute, B.V.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import contextlib
import dataclasses
import datetime
import functools
import operator
from typing import Any
from typing import Callable
from typing import Final
from typing import Union

from tyminator.util import monkey_patch

Change = Union[int, float, datetime.timedelta]
Step = Union[int, datetime.timedelta]
Action = Callable[["Clock"], None]

_ZERO_TIMEDELTA: Final = datetime.timedelta()


class LockError(Exception):
    """Raised when trying to take a step when clock not ready."""


def from_step(step: Step) -> datetime.timedelta:
    if isinstance(step, int):
        return datetime.timedelta(seconds=step)
    else:
        return step


def from_change(change: Change) -> datetime.timedelta:
    if isinstance(change, int):
        change = float(change)
    if isinstance(change, float):
        return datetime.timedelta(seconds=change)
    else:
        return change


class Clock:
    @dataclasses.dataclass(frozen=True, eq=False)
    class __Event:
        when: datetime.datetime
        action: Action
        sequence: int

        SORT_KEY = operator.attrgetter("when", "sequence")

    __current_datetime: datetime.datetime
    __start: datetime.datetime
    __utc_start: datetime.datetime
    __local_tz: datetime.tzinfo
    __step: datetime.timedelta
    __is_locked: bool = False
    __event_queue: list[__Event] = []
    __mark_seq: int = 0
    __event_seq: int = 0

    def __init__(
        self,
        start: datetime.datetime,
        step: Step = 1,
        *,
        local_tz: datetime.tzinfo = datetime.timezone.utc,
    ):
        if start.tzinfo is not None:
            raise ValueError("start may not have tzinfo")
        self.__start = self.__current_datetime = start
        self.__local_tz = local_tz

        self.__step = from_step(step)

    @property
    def current_datetime(self) -> datetime.datetime:
        return self.__current_datetime

    @property
    def current_tz_datetime(self) -> datetime.datetime:
        return self.__current_datetime.replace(tzinfo=self.__local_tz)

    @property
    def current_utc_datetime(self) -> datetime.datetime:
        return self.current_tz_datetime.astimezone(datetime.timezone.utc)

    @property
    def current_timestamp(self) -> float:
        return self.__current_datetime.timestamp()

    @property
    def current_tz_timestamp(self) -> float:
        return self.current_tz_datetime.timestamp()

    @property
    def current_utc_timestamp(self) -> float:
        return self.current_utc_datetime.timestamp()

    @property
    def elapsed(self) -> datetime.timedelta:
        return self.current_tz_datetime - self.tz_start

    @property
    def local_tz(self):
        return self.__local_tz

    @property
    def start(self) -> datetime.datetime:
        return self.__start

    @functools.cached_property
    def tz_start(self) -> datetime.datetime:
        return self.as_tz(self.__start)

    @functools.cached_property
    def utc_start(self) -> datetime.datetime:
        return self.as_utc(self.__start)

    @property
    def step(self) -> datetime.timedelta:
        return self.__step

    @property
    def is_locked(self) -> bool:
        return self.__is_locked

    def as_naive(self, dt: datetime.datetime):
        if dt.tzinfo is not None:
            if dt.tzinfo != self.__local_tz:
                dt = self.as_tz(dt)
            dt = dt.replace(tzinfo=None)
        return dt

    def as_tz(self, dt: datetime.datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.local_tz)
        else:
            return dt.astimezone(self.local_tz)

    def as_utc(self, dt: datetime.datetime):
        if dt.tzinfo is None:
            dt = self.as_tz(dt)
        return dt.astimezone(datetime.timezone.utc)

    def __run_pending_events(self, until: datetime.datetime):
        while self.__event_queue and (event := self.__event_queue[0]).when <= until:
            self.__current_datetime = event.when
            del self.__event_queue[0]
            action = event.action
            if asyncio.iscoroutinefunction(action):
                raise NotImplementedError
            else:
                action(self)

    def elapse(self, change: Change) -> None:
        change = from_change(change)
        if change < _ZERO_TIMEDELTA:
            raise ValueError("change must be positive or zero")

        with self.lock():
            next_datetime = self.__current_datetime + change
            self.__run_pending_events(next_datetime)
            self.__current_datetime = next_datetime

    def elapse_steps(self, steps: int = 1) -> None:
        return self.elapse(self.step * steps)

    def next_datetime(self) -> datetime.datetime:
        current_datetime = self.__current_datetime
        self.elapse_steps()
        return current_datetime

    def next_tz_datetime(self) -> datetime.datetime:
        return self.as_tz(self.next_datetime())

    def next_utc_datetime(self) -> datetime.datetime:
        return self.as_utc(self.next_tz_datetime())

    def time_function(self) -> float:
        try:
            return self.next_timestamp()
        except LockError:
            return self.current_timestamp

    def sleep_function(self, secs) -> None:
        asyncio.run(self.async_sleep_function(secs))

    async def async_sleep_function(self, delay, result=None, *, loop=None) -> Any:
        if loop is not None:
            raise NotImplementedError("loop parameter is unsupported")
        if not isinstance(delay, (int, float)):
            raise TypeError("must be int or float")
        delay = float(delay)
        self.elapse(delay)
        return result

    def next_timestamp(self) -> float:
        current_timestamp = self.current_timestamp
        self.next_datetime()
        return current_timestamp

    def next_tz_timestamp(self) -> float:
        current_tz_timestamp = self.current_tz_timestamp
        self.next_datetime()
        return current_tz_timestamp

    def next_utc_timestamp(self) -> float:
        current_utc_timestamp = self.current_utc_timestamp
        self.next_datetime()
        return current_utc_timestamp

    def dt_at_step(self, step: int) -> datetime.datetime:
        return self.__start + self.__step * step

    def tz_dt_at_step(self, step: int) -> datetime.datetime:
        return self.as_tz(self.dt_at_step(step))

    def utc_dt_at_step(self, step: int) -> datetime.datetime:
        return self.as_utc(self.tz_dt_at_step(step))

    def run_at(self, action: Action, when: datetime.datetime):
        when = self.as_naive(when)
        if when < self.__current_datetime:
            raise ValueError("time must be in the future")
        event = self.__Event(when=when, action=action, sequence=self.__event_seq)
        self.__event_seq += 1
        self.__event_queue.append(event)
        self.__event_queue.sort(key=self.__Event.SORT_KEY)

    def run_in(self, action: Action, change: Change):
        when = self.__current_datetime + from_change(change)
        self.run_at(action, when)

    def run_in_steps(self, action: Action, steps: int):
        change = self.__step * steps
        self.run_in(action, change)

    def mark(self) -> "Mark":
        mark = Mark(self, self.current_datetime, self.__mark_seq)
        self.__mark_seq += 1
        return mark

    @contextlib.contextmanager
    def lock(self):
        if self.__is_locked:
            raise LockError("already locked")
        try:
            self.__is_locked = True
            yield
        finally:
            del self.__is_locked

    @classmethod
    def from_datetime(cls, dt: datetime.datetime, step: Step = 1) -> "Clock":
        if dt.tzinfo is not None:
            local_tz = dt.tzinfo
            dt = dt.replace(tzinfo=None)
        else:
            local_tz = datetime.timezone.utc

        return Clock(dt, step, local_tz=local_tz)


@dataclasses.dataclass(frozen=True)
@functools.total_ordering
class Mark:

    clock: Clock
    when: datetime.datetime
    seq: int

    @functools.cached_property
    def tz_when(self) -> datetime.datetime:
        return self.clock.as_tz(self.when)

    @functools.cached_property
    def utc_when(self) -> datetime.datetime:
        return self.clock.as_utc(self.tz_when)

    @functools.cached_property
    def elapsed(self) -> datetime.timedelta:
        return self.when - self.clock.start

    def __lt__(self, other) -> bool:
        if isinstance(other, Mark) and self.clock is other.clock:
            return (self.when, self.seq) < (other.when, other.seq)
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, int):
            other = from_step(other)

        if isinstance(other, datetime.timedelta):
            return self.when + other

        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, int):
            other = from_step(other)

        if isinstance(other, Mark):
            other = other.when

        if isinstance(other, datetime.datetime):
            other = self.clock.as_naive(other)

        if isinstance(other, (datetime.timedelta, datetime.datetime)):
            return self.when - other

        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, datetime.datetime):
            other = self.clock.as_naive(other)
            return other - self.when

        return NotImplemented


@contextlib.contextmanager
def installed(
    clock: Union[Clock, datetime.datetime],
    *,
    time: Any = monkey_patch.Spec("time", "time"),
    sleep: Any = monkey_patch.Spec("time", "sleep"),
    async_sleep: Any = monkey_patch.Spec("asyncio", "sleep"),
):
    if isinstance(clock, datetime.datetime):
        clock = Clock.from_datetime(clock)

    time_functions = monkey_patch.PatchSet(
        time=time, sleep=sleep, async_sleep=async_sleep
    )
    try:
        time_functions.install(
            time=clock.time_function,
            sleep=clock.sleep_function,
            async_sleep=clock.async_sleep_function,
        )
        yield time_functions, clock
    finally:
        time_functions.restore()


__all__ = (
    "Action",
    "Change",
    "Clock",
    "LockError",
    "Mark",
    "Step",
    "from_change",
    "from_step",
    "installed",
)
