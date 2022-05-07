import datetime
import functools


class Clock:

    __current_datetime: datetime.datetime
    __epoch: datetime.datetime
    __epoch_utc: datetime.datetime
    __local_tz: datetime.tzinfo

    def __init__(
        self,
        epoch: datetime.datetime,
        *,
        local_tz: datetime.tzinfo = datetime.timezone.utc,
    ):
        self.__current_datetime = epoch
        if epoch.tzinfo is None:
            epoch = epoch.replace(tzinfo=local_tz)
        self.__epoch = epoch
        self.__local_tz = local_tz

    @property
    def current_datetime(self) -> datetime.datetime:
        return self.__current_datetime

    @property
    def tz_current_datetime(self) -> datetime.datetime:
        current_datetime = self.__current_datetime
        if current_datetime.tzinfo is None:
            return current_datetime.replace(tzinfo=self.__local_tz)
        else:
            return current_datetime

    @property
    def utc_current_datetime(self) -> datetime.datetime:
        return self.tz_current_datetime.astimezone(datetime.timezone.utc)

    @property
    def epoch(self):
        return self.__epoch

    @functools.cached_property
    def utc_epoch(self) -> datetime.datetime:
        return self.__epoch.astimezone(datetime.timezone.utc)


__all__ = [
    "Clock",
]
