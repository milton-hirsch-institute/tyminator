def test_timing_plugin(pytester):

    pytester.makepyfile(
        """
        import datetime

        def test_clock(clock, clock_local_tz, clock_start, clock_step):
            assert clock.local_tz == clock_local_tz
            assert clock.start == clock_start
            assert clock.step == datetime.timedelta(seconds=clock_step)
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
