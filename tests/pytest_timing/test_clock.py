import datetime
import time

import pytest

from pytest_timing import clock as clock_module


class TestAsTimedelta:
    @staticmethod
    @pytest.mark.parametrize("int_step", range(-4, 1))
    def test_invalid_int(int_step):
        with pytest.raises(ValueError, match=r"^step must be positive integer$"):
            clock_module.as_timedelta(int_step)

    @staticmethod
    @pytest.mark.parametrize("int_step", range(1, 5))
    def test_int(int_step):
        expected = datetime.timedelta(seconds=int_step)
        assert clock_module.as_timedelta(int_step) == expected

    @staticmethod
    @pytest.mark.parametrize("int_step", range(1, 5))
    def test_timedelta(int_step):
        expected = datetime.timedelta(seconds=int_step)
        assert clock_module.as_timedelta(expected) is expected


class TestConstructor:
    @staticmethod
    def test_tz_epoch(clock_epoch, clock_local_tz):
        tz_epoch = clock_epoch.replace(tzinfo=clock_local_tz)
        with pytest.raises(ValueError, match=r"^Epoch may not have tzinfo$"):
            clock_module.Clock(tz_epoch, clock_local_tz)

    @staticmethod
    def test_epoch(clock, clock_epoch, clock_local_tz):
        assert clock.epoch == clock_epoch
        clock_tz_epoch = clock_epoch.replace(tzinfo=clock_local_tz)
        assert clock.tz_epoch == clock_tz_epoch
        clock_utc_epoch = clock_tz_epoch.astimezone(datetime.timezone.utc)
        assert clock.utc_epoch == clock_utc_epoch

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

    def test_current_timestamp(self, clock, clock_epoch, clock_local_tz):
        assert clock.current_timestamp == clock_epoch.timestamp()
        clock_tz_epoch = clock_epoch.replace(tzinfo=clock_local_tz)
        assert clock.current_tz_timestamp == clock_tz_epoch.timestamp()
        clock_utf_epoch = clock_tz_epoch.astimezone(datetime.timezone.utc)
        assert clock.current_utc_timestamp == clock_utf_epoch.timestamp()

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

    class TestElapse:
        @staticmethod
        @pytest.mark.parametrize("steps", range(-4, 1))
        def test_invalid_steps(clock, steps):
            with pytest.raises(ValueError, match="^steps must be positive integer$"):
                clock.elapse(steps)

        @staticmethod
        @pytest.mark.parametrize("steps", range(1, 5))
        def test_valid_steps(clock, steps):
            clock.elapse(steps)
            assert clock.current_tz_datetime == clock.tz_epoch + (clock.step * steps)

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

        @staticmethod
        def test_timestamp(clock, clock_epoch):
            for step in range(4):
                next_timestamp = clock.next_timestamp()
                assert next_timestamp == (clock_epoch + clock.step * step).timestamp()
                assert (
                    next_timestamp == (clock.current_datetime - clock.step).timestamp()
                )

        @staticmethod
        def test_tz_timestamp(clock, clock_epoch):
            for step in range(4):
                next_tz_timestamp = clock.next_tz_timestamp()
                assert (
                    next_tz_timestamp
                    == (clock.current_tz_datetime - clock.step).timestamp()
                )

        @staticmethod
        def test_utc_timestamp(clock, clock_epoch):
            for step in range(4):
                next_utc_timestamp = clock.next_utc_timestamp()
                assert (
                    next_utc_timestamp
                    == (clock.current_utc_datetime - clock.step).timestamp()
                )


def test_time_function(clock):
    original_time = time.time
    with clock_module.installed(clock) as (c, time_func):
        assert c is clock
        assert time_func is original_time
        assert time.time == clock.next_timestamp
    assert time.time == original_time
