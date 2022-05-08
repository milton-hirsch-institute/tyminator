import contextlib
import datetime
import functools
import time
from typing import Callable
from typing import Iterator
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
    __epoch: datetime.datetime
    __epoch_utc: datetime.datetime
    __local_tz: datetime.tzinfo
    __step: datetime.timedelta

    def __init__(
        self,
        epoch: datetime.datetime,
        step: ClockStep = 1,
        *,
        local_tz: datetime.tzinfo = datetime.timezone.utc,
    ):
        self.__current_datetime = epoch
        if epoch.tzinfo is None:
            epoch = epoch.replace(tzinfo=local_tz)
        self.__epoch = epoch
        self.__local_tz = local_tz

        self.__step = as_timedelta(step)

    @property
    def current_datetime(self) -> datetime.datetime:
        return self.__current_datetime

    @property
    def current_tz_datetime(self) -> datetime.datetime:
        return self.__to_tz_datetime(self.__current_datetime)

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
        return self.current_tz_datetime - self.epoch

    @property
    def epoch(self) -> datetime.datetime:
        return self.__epoch

    @functools.cached_property
    def utc_epoch(self) -> datetime.datetime:
        return self.__epoch.astimezone(datetime.timezone.utc)

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
        return self.__to_tz_datetime(self.next_datetime())

    def next_utc_datetime(self) -> datetime.datetime:
        return self.next_tz_datetime().astimezone(datetime.timezone.utc)

    def next_timestamp(self) -> float:
        self.next_datetime()
        return self.current_timestamp

    def next_tz_timestamp(self) -> float:
        self.next_datetime()
        return self.current_tz_timestamp

    def next_utc_timestamp(self) -> float:
        self.next_datetime()
        return self.current_utc_timestamp

    def __to_tz_datetime(self, dt: datetime.datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.__local_tz)
        else:
            return dt


@contextlib.contextmanager
def installed(clock: Clock) -> Iterator[tuple[Clock, Callable[[], float]]]:
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
