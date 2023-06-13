# Copyright 2023 Rafe Kaplan
# SPDX-License-Identifier: Apache-2.0

import datetime

import pytest

from tyminator import clock as clock_module
from tyminator import defaults


@pytest.fixture
def clock(clock_start, clock_step, clock_local_tz) -> clock_module.Clock:
    return clock_module.Clock(clock_start, clock_step, local_tz=clock_local_tz)


@pytest.fixture
def clock_start() -> datetime.datetime:
    return defaults.DEFAULT_CLOCK_START


@pytest.fixture
def clock_local_tz() -> datetime.tzinfo:
    return defaults.DEFAULT_LOCAL_TZ


@pytest.fixture
def clock_step() -> clock_module.Step:
    return 1


__all__ = (
    "clock",
    "clock_local_tz",
    "clock_start",
    "clock_step",
)
