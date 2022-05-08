import contextlib
import datetime
import functools
import time
from typing import Union

ClockStep = Union[int, datetime.timedelta]


def as_timedelta(step: ClockStep) -> datetime.timedelta:
    if isinstance(step, int):
        if step <= 0:
            raise ValueError("step must be positive integer")
        return datetime.timedelta(seconds=step)
    else:
        return step


class Clock:

    __current_datetime: datetime.datetime
    __start: datetime.datetime
    __utc_start: datetime.datetime
    __local_tz: datetime.tzinfo
    __step: datetime.timedelta

    def __init__(
        self,
        start: datetime.datetime,
        step: ClockStep = 1,
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
    def elapsed_time(self) -> datetime.timedelta:
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

    def elapse(self, steps: int) -> None:
        if steps <= 0:
            raise ValueError("steps must be positive integer")
        self.__current_datetime = self.__current_datetime + self.step * steps

    def next_datetime(self) -> datetime.datetime:
        current_datetime = self.__current_datetime
        self.elapse(1)
        return current_datetime

    def next_tz_datetime(self) -> datetime.datetime:
        return self.next_datetime().replace(tzinfo=self.__local_tz)

    def next_utc_datetime(self) -> datetime.datetime:
        return self.next_tz_datetime().astimezone(datetime.timezone.utc)

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


@contextlib.contextmanager
def installed(clock: Clock):
    original_time = time.time
    try:
        time.time = clock.next_timestamp
        yield clock, original_time
    finally:
        time.time = original_time


__all__ = (
    "Clock",
    "ClockStep",
    "as_timedelta",
    "installed",
)
