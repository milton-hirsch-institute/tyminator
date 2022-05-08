import datetime

import pytest

from pytest_timing import clock as clock_module
from pytest_timing import defaults


@pytest.fixture
def clock(clock_epoch, clock_step, clock_local_tz) -> clock_module.Clock:
    return clock_module.Clock(clock_epoch, clock_step, local_tz=clock_local_tz)


@pytest.fixture
def clock_epoch() -> datetime.datetime:
    return defaults.DEFAULT_EPOCH


@pytest.fixture
def clock_local_tz() -> datetime.tzinfo:
    return defaults.DEFAULT_LOCAL_TZ


@pytest.fixture
def clock_step() -> clock_module.ClockStep:
    return 1
