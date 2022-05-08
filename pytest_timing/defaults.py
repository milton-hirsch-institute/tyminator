import datetime

DEFAULT_LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=2))
DEFAULT_EPOCH = datetime.datetime(2014, 7, 28, 14, 30)

__all__ = (
    "DEFAULT_EPOCH",
    "DEFAULT_LOCAL_TZ",
)
