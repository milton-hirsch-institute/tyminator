import datetime

import pytest

from tests.pytest_timing import const


@pytest.mark.parametrize("clock_epoch", const.DEFAULT_EPOCHS)
class TestConstructor:
    @staticmethod
    def test_epoch(clock, clock_epoch, clock_local_tz):
        tz_epoch = clock_epoch.replace(tzinfo=clock_local_tz)
        assert clock.epoch == tz_epoch
        assert clock.utc_epoch == tz_epoch

    @staticmethod
    def test_current_datetime(clock, clock_epoch, clock_step):
        assert clock.current_datetime == clock_epoch

    @staticmethod
    def test_current_tz_datetime(clock, clock_epoch, clock_local_tz):
        expected = clock_epoch.replace(tzinfo=clock_local_tz)
        assert clock.current_tz_datetime == expected

    @staticmethod
    @pytest.mark.parametrize(
        "clock_step,expected",
        [
            (1, datetime.timedelta(seconds=1)),
            (2, datetime.timedelta(seconds=2)),
            (3, datetime.timedelta(seconds=3)),
            (4, datetime.timedelta(seconds=4)),
        ],
    )
    def test_int_step(clock, expected):
        assert clock.step == expected

    @staticmethod
    @pytest.mark.parametrize("steps", range(3))
    @pytest.mark.parametrize(
        "clock_step", [datetime.timedelta(seconds=1), datetime.timedelta(minutes=2)]
    )
    def test_elapsed(clock, steps, clock_step):
        for _ in range(steps):
            clock.next_datetime()

        assert clock.elapsed_time == clock_step * steps

    @staticmethod
    def test_current_utc_datetime(clock, clock_epoch, clock_local_tz):
        expected = clock_epoch.replace(tzinfo=clock_local_tz)
        expected = expected.astimezone(datetime.timezone.utc)
        assert clock.current_utc_datetime == expected

    @pytest.mark.parametrize("clock_step", [1, 5, datetime.timedelta(minutes=2)])
    class TestNextDatetime:
        @staticmethod
        def test_datetime(clock, clock_epoch):
            for step in range(4):
                next_datetime = clock.next_datetime()
                assert next_datetime == clock_epoch + (clock.step * step)
                assert next_datetime == clock.current_datetime - clock.step

        @staticmethod
        def test_tz_datetime(clock, clock_epoch):
            for step in range(4):
                next_tz_datetime = clock.next_tz_datetime()
                assert next_tz_datetime == clock.current_tz_datetime - clock.step

        @staticmethod
        def test_utc_datetime(clock, clock_epoch):
            for step in range(4):
                next_utc_datetime = clock.next_utc_datetime()
                assert next_utc_datetime == clock.current_utc_datetime - clock.step
