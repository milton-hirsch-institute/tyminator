import datetime

import pytest

from pytest_timing import clock as clock_module


class TestConstructor:
    @staticmethod
    def test_no_tz_epoch(clock, clock_epoch, clock_local_tz):
        tz_epoch = clock_epoch.replace(tzinfo=clock_local_tz)
        assert clock.epoch == tz_epoch
        assert clock.utc_epoch == tz_epoch

    @staticmethod
    def test_tz_epoch(clock_epoch, clock_local_tz):
        tz_epoch = clock_epoch.replace(tzinfo=clock_local_tz)
        new_clock = clock_module.Clock(tz_epoch, local_tz=clock_local_tz)
        assert new_clock.epoch == tz_epoch
        assert new_clock.utc_epoch == tz_epoch

    @staticmethod
    @pytest.mark.parametrize(
        "clock_epoch",
        [
            datetime.datetime(2014, 7, 28, 14, 30),
            datetime.datetime(
                2014,
                7,
                28,
                14,
                30,
                tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
            ),
        ],
    )
    def test_current_datetime(clock, clock_epoch):
        assert clock.current_datetime == clock_epoch

    @staticmethod
    @pytest.mark.parametrize(
        "clock_epoch",
        [
            datetime.datetime(2014, 7, 28, 14, 30),
            datetime.datetime(
                2014,
                7,
                28,
                14,
                30,
                tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
            ),
        ],
    )
    def test_tz_current_datetime(clock, clock_epoch, clock_local_tz):
        expected = clock_epoch.replace(tzinfo=clock_local_tz)
        assert clock.tz_current_datetime == expected

    @staticmethod
    @pytest.mark.parametrize(
        "clock_epoch,expected",
        [
            (
                datetime.datetime(2014, 7, 28, 14, 30),
                datetime.datetime(2014, 7, 28, 12, 30, tzinfo=datetime.timezone.utc),
            ),
            (
                datetime.datetime(
                    2014,
                    7,
                    28,
                    14,
                    30,
                    tzinfo=datetime.timezone(datetime.timedelta(hours=-5)),
                ),
                datetime.datetime(
                    2014,
                    7,
                    28,
                    19,
                    30,
                    tzinfo=datetime.timezone.utc,
                ),
            ),
        ],
    )
    def test_utc_current_datetime(clock, clock_epoch, expected):
        assert clock.utc_current_datetime == expected
