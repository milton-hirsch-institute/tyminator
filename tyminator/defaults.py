# Copyright 2023-2025 The Milton Hirsch Institute, B.V.
# SPDX-License-Identifier: Apache-2.0

import datetime
from typing import Final

DEFAULT_LOCAL_TZ: Final = datetime.timezone(datetime.timedelta(hours=2))
DEFAULT_CLOCK_START: Final = datetime.datetime(2014, 7, 28, 14, 30)

__all__ = (
    "DEFAULT_CLOCK_START",
    "DEFAULT_LOCAL_TZ",
)
