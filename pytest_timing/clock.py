import asyncio
import contextlib
import dataclasses
import datetime
import functools
import operator
import time
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Union
from typing import cast

Change = Union[int, float, datetime.timedelta]
Step = Union[int, datetime.timedelta]
Action = Callable[["Clock"], None]

_ZERO_TIMEDELTA = datetime.timedelta()


class LockError(Exception):
    """Raised when trying to take a step when clock not ready."""


class SyncOnlyError(Exception):
    """Raised when calling a synchronous only function in synchronous code."""


def from_step(step: Any) -> datetime.timedelta:
    if isinstance(step, int):
        return datetime.timedelta(seconds=step)
    elif isinstance(step, datetime.timedelta):
        return step
    else:
        raise TypeError("invalid step")


def from_change(change: Change) -> datetime.timedelta:
    if isinstance(change, int):
        change = float(change)
    if isinstance(change, float):
        return datetime.timedelta(seconds=change)
    elif isinstance(change, datetime.timedelta):
        return change
    else:
        raise TypeError("invalid change")


class Clock:
    @dataclasses.dataclass(frozen=True, eq=False)
    class __Event:
        when: datetime.datetime
        action: Action

        SORT_KEY = operator.attrgetter("when", "action")

    __current_datetime: datetime.datetime
    __start: datetime.datetime
    __utc_start: datetime.datetime
    __local_tz: datetime.tzinfo
    __step: datetime.timedelta
    __is_locked: bool = False
    __event_queue: list[__Event] = cast(list[__Event], [])
    __mark_seq: int = 0

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

    def as_unaware(self, dt: datetime.datetime):
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

    async def __run_pending_events(self, until: datetime.datetime):
        while self.__event_queue and (event := self.__event_queue[0]).when <= until:
            self.__current_datetime = event.when
            del self.__event_queue[0]
            action = event.action
            if asyncio.iscoroutinefunction(action):
                await cast(Awaitable, action(self))
            else:
                action(self)

    async def async_elapse(self, change: Change) -> None:
        change = from_change(change)
        if change < _ZERO_TIMEDELTA:
            raise ValueError("change must be positive or zero")

        with self.lock():
            next_datetime = self.__current_datetime + change
            await self.__run_pending_events(next_datetime)
            self.__current_datetime = next_datetime

    async def async_elapse_steps(self, steps: int = 1) -> None:
        return await self.async_elapse(self.step * steps)

    def elapse(self, change: Change) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.async_elapse(change))
        else:
            raise SyncOnlyError("only callable from synchronous functions")

    def elapse_steps(self, steps: int = 1):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.async_elapse_steps(steps))
        else:
            raise SyncOnlyError("only callable from synchronous functions")

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
        except (LockError, SyncOnlyError):
            pass
        return self.current_timestamp

    def sleep_function(self, secs) -> None:
        asyncio.run(self.async_sleep_function(secs))

    async def async_sleep_function(self, delay, result=None, *, loop=None) -> Any:
        if loop is not None:
            raise NotImplementedError("loop parameter is unsupported")
        if not isinstance(delay, (int, float)):
            raise TypeError("must be int or float")
        delay = float(delay)
        await self.async_elapse(delay)
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
        when = self.as_unaware(when)
        if when < self.__current_datetime:
            raise ValueError("time must be in the future")
        event = self.__Event(when=when, action=action)
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
    def elpased(self) -> datetime.timedelta:
        return self.when - self.clock.start

    def __lt__(self, other) -> bool:
        if isinstance(other, Mark) and self.clock is other.clock:
            return (self.when, self.seq) < (other.when, other.seq)
        else:
            return NotImplemented

    def __add__(self, other) -> bool:
        if isinstance(other, int):
            other = from_step(other)

        if isinstance(other, datetime.timedelta):
            return self.when + other

        return NotImplemented

    def __sub__(self, other) -> bool:
        if isinstance(other, int):
            other = from_step(other)

        if isinstance(other, Mark):
            other = other.when

        if isinstance(other, (datetime.timedelta, datetime.datetime)):
            return self.when - other

        return NotImplemented


@dataclasses.dataclass(frozen=True)
class TimeFunctions:
    time: Callable
    sleep: Callable
    async_sleep: Callable

    @classmethod
    def save(cls):
        return cls(time.time, time.sleep, asyncio.sleep)

    def install(self):
        time.time

    def restore(self):
        time.time = self.time
        time.sleep = self.sleep
        asyncio.sleep = self.async_sleep


@contextlib.contextmanager
def installed(clock: Clock):
    original_functions = TimeFunctions.save()
    try:
        time.time = clock.time_function
        time.sleep = clock.sleep_function
        asyncio.sleep = clock.async_sleep_function
        yield original_functions
    finally:
        original_functions.restore()


__all__ = (
    "Action",
    "Change",
    "Clock",
    "LockError",
    "Mark",
    "Step",
    "SyncOnlyError",
    "TimeFunctions",
    "from_change",
    "from_step",
    "installed",
)
