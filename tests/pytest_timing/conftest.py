import datetime

import pytest

from pytest_timing import clock as clock_module


@pytest.fixture
def clock(clock_epoch, clock_local_tz) -> clock_module.Clock:
    return clock_module.Clock(clock_epoch, local_tz=clock_local_tz)


@pytest.fixture
def clock_epoch() -> datetime.datetime:
    return datetime.datetime(2014, 7, 28, 14, 30)


@pytest.fixture
def clock_local_tz() -> datetime.tzinfo:
    return datetime.timezone(datetime.timedelta(hours=2))
