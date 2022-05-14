import dataclasses
import datetime
import time

import pytest

from pytest_timing import clock as clock_module
from pytest_timing import defaults


async def no_op():
    pass


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

    @pytest.mark.asyncio
    class TestAsyncElapse:
        @staticmethod
        @pytest.mark.parametrize("steps", range(-4, 1))
        async def test_invalid_steps(clock, steps):
            with pytest.raises(ValueError, match="^steps must be positive integer$"):
                await clock.async_elapse(steps)

        @staticmethod
        async def test_locked(clock):
            with clock.lock():
                with pytest.raises(clock_module.LockError, match="^already locked$"):
                    await clock.async_elapse()
                assert clock.current_datetime == clock.start

        @staticmethod
        @pytest.mark.parametrize("steps", range(1, 5))
        async def test_valid_steps(clock, steps):
            await clock.async_elapse(steps)
            assert clock.current_tz_datetime == clock.tz_start + (clock.step * steps)

    class TestElapse:
        @staticmethod
        def test_sync(clock):
            clock.elapse(2)
            assert clock.current_tz_datetime == clock.tz_start + (clock.step * 2)

        @staticmethod
        @pytest.mark.asyncio
        async def test_async(clock):
            with pytest.raises(
                clock_module.SyncOnlyError,
                match="^only callable from synchronous functions$",
            ):
                clock.elapse(2)
            assert clock.current_tz_datetime == clock.tz_start

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

        class TestTimeFunction:
            @staticmethod
            def test_unlocked(clock):
                for step in range(4):
                    next_timestamp = clock.time_function()
                    assert (
                        next_timestamp == (clock.start + clock.step * step).timestamp()
                    )
                    assert (
                        next_timestamp
                        == (clock.current_datetime - clock.step).timestamp()
                    )

            @staticmethod
            def test_locked(clock):
                with clock.lock():
                    for step in range(4):
                        next_timestamp = clock.time_function()
                        assert next_timestamp == clock.start.timestamp()
                        assert clock.current_timestamp == next_timestamp

            @staticmethod
            @pytest.mark.asyncio
            async def test_async(clock, clock_step):
                clock.time_function()
                assert clock.current_datetime == clock.start

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

    class TestRunInSteps:
        @staticmethod
        @pytest.mark.parametrize("steps", range(-5, 0))
        def test_negative_steps(clock, steps, call_collector):
            with pytest.raises(ValueError, match=r"^steps must be positive integer$"):
                clock.run_in_steps(call_collector, steps)

        @staticmethod
        def test_run_at_beginning(clock, call_collector):
            clock.run_in_steps(call_collector, 0)
            clock.elapse()
            assert call_collector.calls == [clock.start]

        @staticmethod
        def test_run_at_end(clock, call_collector):
            clock.run_in_steps(call_collector, 1)
            clock.elapse()
            assert call_collector.calls == [clock.start + clock.step]

        @staticmethod
        def test_run_all(clock, call_collector):
            clock.run_in_steps(call_collector, 1)
            clock.run_in_steps(call_collector, 2)
            clock.run_in_steps(call_collector, 2)
            clock.run_in_steps(call_collector, 3)
            clock.elapse(3)
            assert call_collector.calls == [
                clock.start + clock.step,
                clock.start + clock.step * 2,
                clock.start + clock.step * 2,
                clock.start + clock.step * 3,
            ]

        @staticmethod
        def test_async(clock, call_collector):
            clock.run_in_steps(call_collector.as_async, 1)
            clock.run_in_steps(call_collector.as_async, 2)
            clock.run_in_steps(call_collector.as_async, 2)
            clock.run_in_steps(call_collector.as_async, 3)
            clock.elapse(3)
            assert call_collector.calls == [
                clock.start + clock.step,
                clock.start + clock.step * 2,
                clock.start + clock.step * 2,
                clock.start + clock.step * 3,
            ]

    @staticmethod
    def test_mark(clock):
        mark1 = clock.mark()
        clock.elapse()
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
            clock.elapse()
            m2 = clock.mark()
            assert m1 < m2

        @staticmethod
        def test_general_sorting(clock):
            m1 = clock.mark()
            clock.elapse()
            m2 = clock.mark()
            clock.elapse()
            m3 = clock.mark()
            m4 = clock.mark()
            clock.elapse()
            m5 = clock.mark()
            unordered = [m2, m4, m1, m5, m3]
            assert sorted(unordered) == [m1, m2, m3, m4, m5]

    class TestAdd:
        @staticmethod
        @pytest.fixture
        def mark(clock):
            clock.elapse()
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


def test_install(clock):
    original_time = time.time
    with clock_module.installed(clock) as (c, time_func):
        assert c is clock
        assert time_func is original_time
        assert time.time == clock.time_function
    assert time.time == original_time
