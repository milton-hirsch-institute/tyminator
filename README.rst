..
    Copyright 2023 The Milton Hirsch Institute, B.V.
    SPDX-License-Identifier: Apache-2.0


Tyminator
=========

Are you tired of unpredictable time values messing with your testing?  Enter Tyminator, a testing
toolkit that terminates uncertainty and boosts the reliability of your tests.

Just like how database fixtures provide predictable data sets, Tyminator brings that same level of
predictability to time. Tyminator enables precise control over time-related operations in
testing scenarios by seamlessly replacing the built-in Python time functions.

Importance of Predictable Time Test Fixtures
--------------------------------------------

Test fixtures are the guardians of correctness and stability in software applications, setting the
stage for tests with data, dependencies, and environment configurations. But when it comes to
time-sensitive operations like scheduling events or handling timeouts, relying on the actual
passage of time introduces non-deterministic behavior, making it challenging to reproduce and
debug issues consistently.

By controlling time, developers can isolate specific scenarios, simulate time-based events, and
test edge cases that would otherwise be difficult to replicate reliably. This control allows for
comprehensive testing of time-sensitive functionality, including handling time zones, time-based
calculations, and scheduling logic.

Key features
------------

The library offers a range of features and methods to manipulate time, schedule events, calculate
durations, and track elapsed time, ensuring accurate and repeatable test results.

* Patching Time Functions: Tyminator seamlessly replaces the built-in Python time functions with a fake clock implementation. This allows tests to control and manipulate time-related operations without affecting or being affected by the actual system time.
* Fine-Grained Time Manipulation: Test fixtures can move time forward in controlled increments, making it possible to simulate various time-based scenarios accurately. This enables comprehensive testing of time-dependent code paths.
* Predictable Timestamp Generation: Test fixtures can generate consistent and predictable timestamps, eliminating non-deterministic behavior associated with real-time values. This ensures reliable test results and simplifies debugging.
* Time Zone Support: Supports simulating alternate local time zones, allowing tests to ensure that time-dependent code handles regional changes correctly.
* Events: Ability to specify specific times when for triggering events, helping to simulate specific sequences of normally unpredictable sequences in asynchronous code paths.

Installation
------------

Tyminator is available as the Python ``tyminator`` package.

For example, to install using `pip`_:

.. code-block:: shell

    $ pip install tyminator

.. _pip: https://github.com/pypa/pip

Usage with unittests
--------------------

.. code-block:: python


    import time
    import unittest
    from datetime import datetime, timezone
    from datetime import timedelta

    from tyminator.clock import Clock
    from tyminator.clock import installed

    EPOCH = datetime(2016, 8, 29, 18, 18)
    EASTERN_TIME = timedelta(hours=-5)

    class MyTimeTest(unittest.TestCase):
        def setUp(self):
            self.clock = Clock(EPOCH, local_tz=timezone(EASTERN_TIME))

        def test_example(self):
            with installed(self.clock):
                now1 = datetime.fromtimestamp(time.time())
                assert now1 == EPOCH

                now2 = datetime.fromtimestamp(time.time())
                assert now2 == EPOCH + self.clock.step

                naive_utc = EPOCH + self.clock.step * 2 - EASTERN_TIME
                assert self.clock.current_utc_datetime == naive_utc.replace(tzinfo=timezone.utc)

Links
-----

-   PyPI Releases: https://pypi.org/project/tyminator/
-   Source Code: https://github.com/milton-hirsch-institute/tyminator
-   Issue Tracker: https://github.com/milton-hirsch-institute/tyminator/issues
