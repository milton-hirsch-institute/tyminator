import datetime
import functools
from typing import Union

ClockStep = Union[int, datetime.timedelta]


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

        if isinstance(step, int):
            step = datetime.timedelta(seconds=step)
        self.__step = step

    @property
    def current_datetime(self) -> datetime.datetime:
        return self.__current_datetime

    @property
    def tz_current_datetime(self) -> datetime.datetime:
        return self.__to_tz_datetime(self.__current_datetime)

    @property
    def utc_current_datetime(self) -> datetime.datetime:
        return self.tz_current_datetime.astimezone(datetime.timezone.utc)

    @property
    def elapsed_time(self) -> datetime.timedelta:
        return self.tz_current_datetime - self.epoch

    @property
    def epoch(self):
        return self.__epoch

    @functools.cached_property
    def utc_epoch(self) -> datetime.datetime:
        return self.__epoch.astimezone(datetime.timezone.utc)

    @property
    def step(self):
        return self.__step

    def next_datetime(self) -> datetime.datetime:
        current_datetime = self.__current_datetime
        self.__current_datetime = current_datetime + self.__step
        return current_datetime

    def next_tz_datetime(self) -> datetime.datetime:
        return self.__to_tz_datetime(self.next_datetime())

    def next_utc_datetime(self) -> datetime.datetime:
        return self.next_tz_datetime().astimezone(datetime.timezone.utc)

    def __to_tz_datetime(self, dt: datetime.datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.__local_tz)
        else:
            return dt


__all__ = [
    "Clock",
]
