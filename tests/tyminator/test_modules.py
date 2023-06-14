# Copyright 2023 Rafe Kaplan
# SPDX-License-Identifier: Apache-2.0

import types
import typing

import pytest

from tyminator import clock
from tyminator import defaults
from tyminator.util import monkey_patch

TYPING_VALUE_IDS = {id(v := getattr(typing, s)): v for s in dir(typing)}


@pytest.mark.parametrize("module", [clock, defaults, monkey_patch])
class TestModule:
    @staticmethod
    def test_has_all(module):
        assert hasattr(module, "__all__")
        assert isinstance(module.__all__, tuple)

    @staticmethod
    def test_all_string(module):
        for symbol in module.__all__:
            assert isinstance(symbol, str)

    @staticmethod
    def test_all_public(module):
        for symbol in module.__all__:
            assert not symbol.startswith("_")

    @staticmethod
    def test_no_modules(module):
        for symbol in module.__all__:
            value = getattr(module, symbol)
            assert not isinstance(value, types.ModuleType)

    @staticmethod
    def test_no_typing_symbols(module):
        for symbol in module.__all__:
            value = getattr(module, symbol)
            assert id(value) not in TYPING_VALUE_IDS

    @staticmethod
    def test_no_missing(module):
        all_symbols = set(module.__all__)
        for symbol in dir(module):
            value = getattr(module, symbol)
            if not (
                symbol.startswith("_")
                or isinstance(value, types.ModuleType)
                or isinstance(value, typing.TypeVar)
                or id(value) in TYPING_VALUE_IDS
            ):
                assert symbol in all_symbols

    @staticmethod
    def test_all_sorted(module):
        assert module.__all__ == tuple(sorted(module.__all__))
