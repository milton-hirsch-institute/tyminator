# Copyright 2023 Rafe Kaplan
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dataclasses
import datetime
import importlib
import time

import pytest

from tests.tyminator import target_module
from tyminator import clock as clock_module
from tyminator import defaults


@dataclasses.dataclass(frozen=True)
class CallCollector:
    clock: clock_module.Clock
    calls: list[datetime.datetime] = dataclasses.field(default_factory=list)

    def __call__(self, clock: clock_module.Clock):
        assert clock is self.clock
        self.calls.append(clock.current_datetime)

    async def as_async(self, clock: clock_module.Clock):
        self(clock)


@pytest.fixture
def call_collector(clock) -> CallCollector:
    return CallCollector(clock)


@pytest.fixture(autouse=True)
def reloaded_target_module():
    try:
        yield
    finally:
        importlib.reload(target_module)


class TestFromStep:
    @staticmethod
    @pytest.mark.parametrize("int_step", range(1, 5))
    def test_int(int_step):
        expected = datetime.timedelta(seconds=int_step)
        assert clock_module.from_step(int_step) == expected

    @staticmethod
    @pytest.mark.parametrize("int_step", range(1, 5))
    def test_timedelta(int_step):
        expected = datetime.timedelta(seconds=int_step)
        assert clock_module.from_step(expected) is expected


class TestFromChange:
    @staticmethod
    @pytest.mark.parametrize(
        "number_change",
        [*range(-2, 3), *[i * 0.5 for i in range(-2, 3)]],
    )
    def test_numbers(number_change):
        expected = datetime.timedelta(seconds=number_change)
        assert clock_module.from_change(number_change) == expected

    @staticmethod
    @pytest.mark.parametrize(
        "timedelta_change", [datetime.timedelta(seconds=i * 0.5) for i in range(-2, 3)]
    )
    def test_timedelta(timedelta_change):
        assert clock_module.from_change(timedelta_change) is timedelta_change


class TestClock:
    class TestConstructor:
        @staticmethod
        def test_tz_start(clock_start, clock_local_tz):
            tz_start = clock_start.replace(tzinfo=clock_local_tz)
            with pytest.raises(ValueError, match=r"^start may not have tzinfo$"):
                clock_module.Clock(tz_start, clock_local_tz)

        @staticmethod
        def test_start(clock, clock_start, clock_local_tz):
            assert clock.start == clock_start
            clock_tz_start = clock_start.replace(tzinfo=clock_local_tz)
            assert clock.tz_start == clock_tz_start
            clock_utc_start = clock_tz_start.astimezone(datetime.timezone.utc)
            assert clock.utc_start == clock_utc_start

        @staticmethod
        def test_current_datetime(clock, clock_start, clock_step):
            assert clock.current_datetime == clock_start

        @staticmethod
        def test_current_tz_datetime(clock, clock_start, clock_local_tz):
            expected = clock_start.replace(tzinfo=clock_local_tz)
            assert clock.current_tz_datetime == expected

        @staticmethod
        def test_current_utc_datetime(clock, clock_start, clock_local_tz):
            expected = clock_start.replace(tzinfo=clock_local_tz)
            expected = expected.astimezone(datetime.timezone.utc)
            assert clock.current_utc_datetime == expected

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
        @pytest.mark.parametrize(
            "clock_step",
            [
                datetime.timedelta(seconds=1),
                datetime.timedelta(seconds=2),
                datetime.timedelta(seconds=3),
                datetime.timedelta(seconds=4),
            ],
        )
        def test_timedelta_step(clock, clock_step):
            assert clock.step is clock_step

        def test_current_timestamp(self, clock, clock_start, clock_local_tz):
            assert clock.current_timestamp == clock_start.timestamp()
            clock_tz_start = clock_start.replace(tzinfo=clock_local_tz)
            assert clock.current_tz_timestamp == clock_tz_start.timestamp()
            clock_utf_start = clock_tz_start.astimezone(datetime.timezone.utc)
            assert clock.current_utc_timestamp == clock_utf_start.timestamp()

        def test_local_tz(self, clock, clock_local_tz):
            assert clock.local_tz is clock_local_tz

    @staticmethod
    @pytest.mark.parametrize("steps", range(3))
    @pytest.mark.parametrize(
        "clock_step", [datetime.timedelta(seconds=1), datetime.timedelta(minutes=2)]
    )
    def test_elapsed(clock, steps, clock_step):
        for _ in range(steps):
            clock.next_datetime()

        assert clock.elapsed == clock_step * steps

    @staticmethod
    def test_current_utc_datetime(clock, clock_start, clock_local_tz):
        expected = clock_start.replace(tzinfo=clock_local_tz)
        expected = expected.astimezone(datetime.timezone.utc)
        assert clock.current_utc_datetime == expected

    class TestTzConversion:
        @staticmethod
        @pytest.fixture
        def naive():
            return datetime.datetime(2014, 1, 1, 12)

        @staticmethod
        @pytest.fixture
        def tz(naive):
            return naive.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))

        @staticmethod
        @pytest.fixture
        def utc(tz):
            return tz.astimezone(datetime.timezone.utc)

        class TestAsNaive:
            @staticmethod
            def test_naive(clock, naive):
                assert clock.as_naive(naive) is naive

            @staticmethod
            def test_tz(clock, tz):
                assert clock.as_naive(tz) == datetime.datetime(2014, 1, 1, 21)

            @staticmethod
            def test_utc(clock, utc):
                assert clock.as_naive(utc) == datetime.datetime(2014, 1, 1, 21)

        class TestAsTz:
            @staticmethod
            def test_naive(clock, naive, clock_local_tz):
                assert clock.as_tz(naive) == naive.replace(tzinfo=clock_local_tz)

            @staticmethod
            def test_tz(clock, tz, clock_local_tz):
                assert clock.as_tz(tz) == datetime.datetime(
                    2014, 1, 1, 21, tzinfo=clock_local_tz
                )

            @staticmethod
            def test_utc(clock, utc, clock_local_tz):
                assert clock.as_tz(utc) == datetime.datetime(
                    2014, 1, 1, 21, tzinfo=clock_local_tz
                )

        class TestAsUtc:
            @staticmethod
            def test_naive(clock, naive):
                assert clock.as_utc(naive) == datetime.datetime(
                    2014, 1, 1, 10, tzinfo=datetime.timezone.utc
                )

            @staticmethod
            def test_tz(clock, tz):
                assert clock.as_utc(tz) == datetime.datetime(
                    2014, 1, 1, 19, tzinfo=datetime.timezone.utc
                )

            @staticmethod
            def test_utc(clock, utc):
                assert clock.as_utc(utc) == datetime.datetime(
                    2014, 1, 1, 19, tzinfo=datetime.timezone.utc
                )

    class TestElapse:
        @staticmethod
        @pytest.mark.parametrize(
            "change",
            [
                *range(-3, 0),
                *[datetime.timedelta(seconds=s) for s in range(-3, 0)],
                *[s * 0.5 for s in range(-3, 0)],
            ],
        )
        def test_negative_changes(clock, change):
            with pytest.raises(ValueError, match="^change must be positive"):
                assert clock.elapse(change)

        @staticmethod
        @pytest.mark.parametrize("change", [*range(3), *(s * 0.5 for s in range(3))])
        def test_positive_number(clock, change):
            clock.elapse(change)
            assert clock.current_datetime == clock.start + clock_module.from_change(
                change
            )

        @staticmethod
        @pytest.mark.parametrize(
            "change", [datetime.timedelta(seconds=s) for s in range(1, 3)]
        )
        def test_positive_timedelta(clock, change):
            clock.elapse(change)
            assert clock.current_datetime == clock.start + change

        @staticmethod
        def test_locked(clock):
            with clock.lock():
                with pytest.raises(clock_module.LockError, match="^already locked$"):
                    clock.elapse(clock.step)
                assert clock.current_datetime == clock.start

    @pytest.mark.parametrize("clock_step", [1, 5, datetime.timedelta(minutes=2)])
    class TestNextDatetime:
        @staticmethod
        def test_datetime(clock, clock_start):
            for step in range(4):
                next_datetime = clock.next_datetime()
                assert next_datetime == clock_start + (clock.step * step)
                assert next_datetime == clock.current_datetime - clock.step

        @staticmethod
        def test_tz_datetime(clock, clock_start):
            for step in range(4):
                next_tz_datetime = clock.next_tz_datetime()
                assert next_tz_datetime == clock.current_tz_datetime - clock.step

        @staticmethod
        def test_utc_datetime(clock, clock_start):
            for step in range(4):
                next_utc_datetime = clock.next_utc_datetime()
                assert next_utc_datetime == clock.current_utc_datetime - clock.step

        @staticmethod
        def test_next_timestamp(clock, clock_start):
            for step in range(4):
                next_timestamp = clock.next_timestamp()
                assert next_timestamp == (clock_start + clock.step * step).timestamp()
                assert (
                    next_timestamp == (clock.current_datetime - clock.step).timestamp()
                )

        @staticmethod
        def test_next_tz_timestamp(clock, clock_start):
            for step in range(4):
                next_tz_timestamp = clock.next_tz_timestamp()
                assert (
                    next_tz_timestamp
                    == (clock.current_tz_datetime - clock.step).timestamp()
                )

        @staticmethod
        def test_next_utc_timestamp(clock, clock_start):
            for step in range(4):
                next_utc_timestamp = clock.next_utc_timestamp()
                assert (
                    next_utc_timestamp
                    == (clock.current_utc_datetime - clock.step).timestamp()
                )

        @staticmethod
        def test_dt_at_step(clock):
            for step in range(-3, 4):
                dt_at_step = clock.dt_at_step(step)
                assert dt_at_step == clock.start + (clock.step * step)

        @staticmethod
        def test_dt_tz_at_step(clock):
            for step in range(-3, 4):
                tz_dt_at_step = clock.tz_dt_at_step(step)
                assert tz_dt_at_step == clock.tz_start + (clock.step * step)

        @staticmethod
        def test_dt_utc_at_step(clock):
            for step in range(-3, 4):
                utc_dt_at_step = clock.utc_dt_at_step(step)
                assert utc_dt_at_step == clock.utc_start + (clock.step * step)

    class TestTimeFunction:
        @staticmethod
        def test_unlocked(clock):
            for step in range(4):
                next_timestamp = clock.time_function()
                assert next_timestamp == (clock.start + clock.step * step).timestamp()
                assert (
                    next_timestamp == (clock.current_datetime - clock.step).timestamp()
                )

        @staticmethod
        def test_locked(clock):
            with clock.lock():
                for _ in range(4):
                    next_timestamp = clock.time_function()
                    assert next_timestamp == clock.start.timestamp()
                    assert clock.current_timestamp == next_timestamp

    @staticmethod
    @pytest.mark.parametrize("secs", [0, 1, 2, 0.0, 0.1, 2.2])
    def test_sleep_function(clock, secs):
        clock.sleep_function(secs)
        assert clock.current_datetime == clock.start + clock_module.from_change(secs)

    @pytest.mark.asyncio
    class TestAsyncSleepFunction:
        @staticmethod
        async def test_with_loop(clock):
            loop = asyncio.new_event_loop()
            with pytest.raises(
                NotImplementedError, match=r"loop parameter is unsupported"
            ):
                await clock.async_sleep_function(1, loop=loop)

        @staticmethod
        @pytest.mark.parametrize(
            "bad_secs",
            [None, "2", defaults.DEFAULT_CLOCK_START, datetime.timedelta(seconds=2)],
        )
        async def test_invalid_secs(clock, bad_secs):
            with pytest.raises(TypeError, match=r"^must be int or float$"):
                await clock.async_sleep_function(bad_secs)

        @staticmethod
        @pytest.mark.parametrize("secs", [0, 1, 2, 0.0, 0.1, 2.2])
        async def test_valid_secs(clock, secs):
            result = "a-result"
            assert await clock.async_sleep_function(secs, "a-result") is result
            assert clock.current_datetime == clock.start + clock_module.from_change(
                secs
            )

    class TestRunAt:
        @staticmethod
        @pytest.mark.parametrize("steps", range(-5, 0))
        def test_negative_steps(clock, steps, call_collector):
            delta = datetime.timedelta(seconds=steps)
            when = clock.current_datetime + delta
            with pytest.raises(ValueError, match=r"^time must be in the future$"):
                clock.run_at(call_collector, when)

        @staticmethod
        def test_run_at_async(clock, call_collector):
            clock.run_at(call_collector.as_async, clock.current_datetime)
            with pytest.raises(NotImplementedError):
                clock.elapse_steps()
            assert call_collector.calls == []

        @staticmethod
        def test_run_at_beginning(clock, call_collector):
            clock.run_at(call_collector, clock.current_datetime)
            clock.elapse_steps()
            assert call_collector.calls == [clock.start]

        @staticmethod
        def test_run_at_end(clock, call_collector):
            clock.run_at(call_collector, clock.current_datetime + clock.step)
            clock.elapse_steps()
            assert call_collector.calls == [clock.start + clock.step]

        @staticmethod
        def test_run_all(clock, call_collector):
            d1 = clock.current_datetime + datetime.timedelta(seconds=1)
            d2 = clock.current_datetime + datetime.timedelta(seconds=1.5)
            d3 = clock.current_datetime + datetime.timedelta(seconds=1.5)
            d4 = clock.current_datetime + datetime.timedelta(seconds=2)
            clock.run_at(call_collector, d1)
            clock.run_at(call_collector, d2)
            clock.run_at(call_collector, d3)
            clock.run_at(call_collector, d4)
            clock.elapse_steps(3)
            assert call_collector.calls == [d1, d2, d3, d4]

    @staticmethod
    def test_run_in(clock, call_collector):
        delta1 = datetime.timedelta(seconds=1)
        delta2 = datetime.timedelta(seconds=1.5)
        delta3 = datetime.timedelta(seconds=1.5)
        delta4 = datetime.timedelta(seconds=2)
        clock.run_in(call_collector, delta1)
        clock.run_in(call_collector, delta2)
        clock.run_in(call_collector, delta3)
        clock.run_in(call_collector, delta4)
        clock.elapse_steps(3)
        assert call_collector.calls == [
            clock.start + delta1,
            clock.start + delta2,
            clock.start + delta3,
            clock.start + delta4,
        ]

    @staticmethod
    @pytest.mark.parametrize("clock_step", [1, 2, 3])
    def test_run_in_steps(clock, call_collector):
        clock.run_in_steps(call_collector, 1)
        clock.run_in_steps(call_collector, 2)
        clock.run_in_steps(call_collector, 2)
        clock.run_in_steps(call_collector, 3)
        clock.elapse_steps(3)
        assert call_collector.calls == [
            clock.start + clock.step,
            clock.start + (clock.step * 2),
            clock.start + (clock.step * 2),
            clock.start + (clock.step * 3),
        ]

    @staticmethod
    def test_mark(clock):
        mark1 = clock.mark()
        clock.elapse_steps()
        mark2 = clock.mark()

        assert mark1.clock is clock
        assert mark2.clock is clock

        assert mark1.when == clock.start
        assert mark2.when == clock.current_datetime

        assert mark1.tz_when == clock.tz_start
        assert mark2.tz_when == clock.current_tz_datetime

        assert mark1.utc_when == clock.utc_start
        assert mark2.utc_when == clock.current_utc_datetime

    class TestLock:
        @staticmethod
        def test_is_locked(clock):
            assert not clock.is_locked
            with clock.lock():
                assert clock.is_locked
            assert not clock.is_locked

        @staticmethod
        def test_nested_lock(clock):
            with clock.lock():
                with pytest.raises(clock_module.LockError, match=r"^already locked$"):
                    with clock.lock():
                        pytest.fail("nested locks not supported")

    class TestFromDatetime:
        @staticmethod
        def test_naive():
            dt = datetime.datetime(2018, 11, 11, 11)
            clock = clock_module.Clock.from_datetime(dt, 5)
            assert clock.start == dt
            assert clock.step == datetime.timedelta(seconds=5)
            assert clock.local_tz == datetime.timezone.utc

        @staticmethod
        def test_tz():
            dt = datetime.datetime(
                2018,
                11,
                11,
                11,
                tzinfo=datetime.timezone(datetime.timedelta(seconds=10)),
            )
            clock = clock_module.Clock.from_datetime(dt, 5)
            assert clock.start == dt.replace(tzinfo=None)
            assert clock.step == datetime.timedelta(seconds=5)
            assert clock.local_tz == datetime.timezone(datetime.timedelta(seconds=10))


class TestMark:
    class TestSorting:
        @staticmethod
        @pytest.mark.parametrize("value", [None, 2.0, defaults.DEFAULT_CLOCK_START, 6])
        def test_unsupported(clock, value):
            with pytest.raises(TypeError):
                clock.mark() < value  # type: ignore

        @staticmethod
        def test_different_clocks(clock_start, clock_local_tz):
            m1 = clock_module.Clock(clock_start).mark()
            m2 = clock_module.Clock(clock_start).mark()

            with pytest.raises(TypeError):
                m1 < m2  # type: ignore

        @staticmethod
        def test_same_datetime(clock):
            m1 = clock_module.Mark(clock, clock.current_datetime, 0)
            m2 = clock_module.Mark(clock, clock.current_datetime, 0)
            assert not (m1 < m2)
            assert not (m1 > m2)

        @staticmethod
        def test_same_datetime_from_clock(clock):
            """Sequence number makes them different."""
            m1 = clock.mark()
            m2 = clock.mark()
            assert m1 < m2

        @staticmethod
        def test_different_datetime(clock):
            m1 = clock.mark()
            clock.elapse_steps()
            m2 = clock.mark()
            assert m1 < m2

        @staticmethod
        def test_general_sorting(clock):
            m1 = clock.mark()
            clock.elapse_steps()
            m2 = clock.mark()
            clock.elapse_steps()
            m3 = clock.mark()
            m4 = clock.mark()
            clock.elapse_steps()
            m5 = clock.mark()
            unordered = [m2, m4, m1, m5, m3]
            assert sorted(unordered) == [m1, m2, m3, m4, m5]

    @staticmethod
    def test_elapsed(clock):
        clock.elapse_steps(5)
        mark = clock.mark()
        assert mark.elapsed == (clock.start + (clock.step * 5)) - clock.start

    class TestAdd:
        @staticmethod
        @pytest.fixture
        def mark(clock):
            clock.elapse_steps()
            return clock.mark()

        @staticmethod
        @pytest.mark.parametrize("value", [None, 2.0, defaults.DEFAULT_CLOCK_START])
        def test_unsupported(mark, value):
            with pytest.raises(TypeError):
                mark + value  # type: ignore

        @staticmethod
        @pytest.mark.parametrize("steps", range(-4, 5))
        def test_int(mark, steps):
            assert mark + steps == mark.when + mark.clock.step * steps

        @staticmethod
        @pytest.mark.parametrize("seconds", range(5))
        def test_timedelta(mark, seconds):
            td = datetime.timedelta(seconds=seconds)
            assert mark + td == mark.when + td

    class TestOperators:
        @staticmethod
        @pytest.fixture
        def mark(clock):
            clock.elapse_steps(2)
            return clock.mark()

        class TestAdd:
            @staticmethod
            @pytest.mark.parametrize("value", [None, 2.0, defaults.DEFAULT_CLOCK_START])
            def test_unsupported(mark, value):
                with pytest.raises(TypeError):
                    mark + value  # type: ignore

            @staticmethod
            @pytest.mark.parametrize("steps", range(-4, 5))
            def test_int(mark, steps):
                assert mark + steps == mark.when + mark.clock.step * steps

            @staticmethod
            @pytest.mark.parametrize("seconds", range(5))
            def test_timedelta(mark, seconds):
                td = datetime.timedelta(seconds=seconds)
                assert mark + td == mark.when + td

        class TestSub:
            @staticmethod
            @pytest.mark.parametrize("value", [None, 2.0])
            def test_unsupported(mark, value):
                with pytest.raises(TypeError):
                    mark - value  # type: ignore

            @staticmethod
            @pytest.mark.parametrize("steps", range(-4, 5))
            def test_int(mark, steps):
                assert mark - steps == mark.when - mark.clock.step * steps

            @staticmethod
            @pytest.mark.parametrize("seconds", range(5))
            def test_timedelta(mark, seconds):
                td = datetime.timedelta(seconds=seconds)
                assert mark - td == mark.when - td

            @staticmethod
            def test_datetime(clock, mark):
                assert mark - (
                    clock.current_datetime - datetime.timedelta(seconds=4)
                ) == datetime.timedelta(seconds=4)

            @staticmethod
            def test_tz_datetime(clock, mark):
                dt = clock.current_tz_datetime - datetime.timedelta(seconds=4)
                assert mark - dt == datetime.timedelta(seconds=4)

            @staticmethod
            def test_mark(clock, mark):
                clock.elapse_steps(4)
                other_mark = clock.mark()
                assert other_mark - mark == datetime.timedelta(seconds=4)

        class TestRSub:
            @staticmethod
            @pytest.mark.parametrize(
                "value", [None, 2.0, datetime.timedelta(seconds=3)]
            )
            def test_unsupported(mark, value):
                with pytest.raises(TypeError):
                    value - mark  # type: ignore

            @staticmethod
            def test_datetime(clock, mark):
                dt = clock.current_datetime + datetime.timedelta(seconds=4)
                assert dt - mark == datetime.timedelta(seconds=4)

            @staticmethod
            def test_tz_datetime(clock, mark):
                dt = clock.current_tz_datetime + datetime.timedelta(seconds=4)
                assert dt - mark == datetime.timedelta(seconds=4)


class TestInstalled:
    @staticmethod
    def test_standard(clock):
        original_time = time.time
        original_sleep = time.sleep
        original_async_sleep = asyncio.sleep
        with clock_module.installed(clock) as (time_functions, clk):
            assert time.time == clock.time_function
            assert time.sleep == clock.sleep_function
            assert asyncio.sleep == clock.async_sleep_function
            assert time_functions.time is original_time
            assert time_functions.sleep is original_sleep
            assert time_functions.async_sleep is original_async_sleep
            assert clk is clock
        assert time.time == time_functions.time
        assert time.sleep == time_functions.sleep
        assert asyncio.sleep == time_functions.async_sleep

    @staticmethod
    def test_alternate(clock):
        original_time = target_module.time_func
        original_sleep = target_module.sleep_func
        original_async_sleep = target_module.async_sleep_func
        with clock_module.installed(
            clock,
            time=target_module.time_func,
            sleep=target_module.sleep_func,
            async_sleep=target_module.async_sleep_func,
        ) as (time_functions, clk):
            assert target_module.time_func == clock.time_function
            assert target_module.sleep_func == clock.sleep_function
            assert target_module.async_sleep_func == clock.async_sleep_function
            assert time_functions.time == original_time
            assert time_functions.sleep == original_sleep
            assert time_functions.async_sleep == original_async_sleep
            assert clk is clock
        assert target_module.time_func == time_functions.time
        assert target_module.sleep_func == time_functions.sleep
        assert target_module.async_sleep_func == time_functions.async_sleep

    @staticmethod
    def test_datetime():
        dt = datetime.datetime(2018, 11, 11, 11)
        with clock_module.installed(dt) as (_, clock):
            assert clock.start == dt
            assert clock.step == datetime.timedelta(seconds=1)
            assert clock.local_tz == datetime.timezone.utc

    @staticmethod
    def test_tz_datetime():
        dt = datetime.datetime(
            2018, 11, 11, 11, tzinfo=datetime.timezone(datetime.timedelta(hours=10))
        )
        with clock_module.installed(dt) as (_, clock):
            assert clock.start == dt.replace(tzinfo=None)
            assert clock.step == datetime.timedelta(seconds=1)
            assert clock.local_tz == datetime.timezone(datetime.timedelta(hours=10))
