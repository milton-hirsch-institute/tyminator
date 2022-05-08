import datetime

DEFAULT_LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=2))
DEFAULT_EPOCH = datetime.datetime(2014, 7, 28, 14, 30)
DEFAULT_TZ_EPOCH = DEFAULT_EPOCH.replace(tzinfo=DEFAULT_LOCAL_TZ)
DEFAULT_EPOCHS = DEFAULT_EPOCH, DEFAULT_TZ_EPOCH

__all__ = (
    "DEFAULT_EPOCH",
    "DEFAULT_EPOCHS",
    "DEFAULT_LOCAL_TZ",
    "DEFAULT_TZ_EPOCH",
)
