import contextlib
import dataclasses
import datetime
import functools
import operator
import time
from typing import Callable
from typing import Union
from typing import cast

Step = Union[int, datetime.timedelta]
Action = Callable[["Clock"], None]


class LockError(Exception):
    """Raised when trying to take a step when clock not ready."""


def as_timedelta(step: Step) -> datetime.timedelta:
    if isinstance(step, int):
        if step <= 0:
            raise ValueError("step must be positive integer")
        return datetime.timedelta(seconds=step)
    else:
        return step


class Clock:
    @dataclasses.dataclass(frozen=True)
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

        self.__step = as_timedelta(step)

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
        return self.__start.replace(tzinfo=self.__local_tz)

    @functools.cached_property
    def utc_start(self) -> datetime.datetime:
        return self.tz_start.astimezone(datetime.timezone.utc)

    @property
    def step(self) -> datetime.timedelta:
        return self.__step

    @property
    def is_locked(self) -> bool:
        return self.__is_locked

    def __run_pending_events(self, until: datetime.datetime):
        while self.__event_queue and (event := self.__event_queue[0]).when <= until:
            self.__current_datetime = event.when
            del self.__event_queue[0]
            event.action(self)

    def elapse(self, steps: int = 1) -> None:
        if steps <= 0:
            raise ValueError("steps must be positive integer")
        with self.lock():
            next_datetime = self.__current_datetime + self.step * steps
            self.__run_pending_events(next_datetime)
            self.__current_datetime = next_datetime

    def next_datetime(self) -> datetime.datetime:
        current_datetime = self.__current_datetime
        self.elapse(1)
        return current_datetime

    def next_tz_datetime(self) -> datetime.datetime:
        return self.next_datetime().replace(tzinfo=self.__local_tz)

    def next_utc_datetime(self) -> datetime.datetime:
        return self.next_tz_datetime().astimezone(datetime.timezone.utc)

    def time_function(self) -> float:
        try:
            return self.next_timestamp()
        except LockError:
            return self.current_timestamp

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
        return self.dt_at_step(step).replace(tzinfo=self.__local_tz)

    def utc_dt_at_step(self, step: int) -> datetime.datetime:
        return self.tz_dt_at_step(step).astimezone(datetime.timezone.utc)

    def run_in_steps(self, action: Action, steps: int):
        if steps < 0:
            raise ValueError("steps must be positive integer")
        when = self.current_datetime + (self.__step * steps)
        event = self.__Event(when=when, action=action)
        self.__event_queue.append(event)
        self.__event_queue.sort(key=self.__Event.SORT_KEY)

    @contextlib.contextmanager
    def lock(self):
        if self.__is_locked:
            raise LockError("already locked")
        try:
            self.__is_locked = True
            yield
        finally:
            del self.__is_locked


@contextlib.contextmanager
def installed(clock: Clock):
    original_time = time.time
    try:
        time.time = clock.time_function
        yield clock, original_time
    finally:
        time.time = original_time


__all__ = (
    "Action",
    "Clock",
    "LockError",
    "Step",
    "as_timedelta",
    "installed",
)
