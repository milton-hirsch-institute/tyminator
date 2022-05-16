import importlib
import sys

import pytest

from pytest_timing.util import monkey_patch
from tests.pytest_timing.util import target_module


@pytest.fixture
def top_spec():
    return monkey_patch.Spec(target_module.__name__, "Top")


@pytest.fixture
def nested_spec():
    return monkey_patch.Spec(target_module.__name__, "Top.Nested")


@pytest.fixture
def double_nested_spec():
    return monkey_patch.Spec(target_module.__name__, "Top.Nested.DoubleNested")


class TestSpec:
    class TestName:
        @staticmethod
        def test_top_level(top_spec):
            assert top_spec.name == "Top"

        @staticmethod
        def test_nested(nested_spec):
            assert nested_spec.name == "Nested"

    class TestParentQualifiedName:
        @staticmethod
        def test_top_level(top_spec):
            assert top_spec.parent_qualified_name is None

        @staticmethod
        def test_double_nested(double_nested_spec):
            assert double_nested_spec.parent_qualified_name == "Top.Nested"

    class TestGetModule:
        @staticmethod
        def test_warm(top_spec, nested_spec, double_nested_spec):
            for spec in top_spec, nested_spec, double_nested_spec:
                importlib.import_module(spec.module_name)
                assert spec.get_module() is target_module

        @staticmethod
        def test_cold(top_spec, nested_spec, double_nested_spec):
            original_modules = sys.modules
            sys.modules = dict(original_modules)
            try:
                for spec in top_spec, nested_spec, double_nested_spec:
                    sys.modules.pop(spec.module_name, None)
                    assert spec.get_module().Top.Nested.DoubleNested
            finally:
                sys.modules = original_modules

    @staticmethod
    def test_get_obj(top_spec, nested_spec, double_nested_spec):
        assert top_spec.get_obj() is target_module.Top
        assert nested_spec.get_obj() is target_module.Top.Nested
        assert double_nested_spec.get_obj() is target_module.Top.Nested.DoubleNested

    @staticmethod
    def test_from_target(top_spec, nested_spec, double_nested_spec):
        assert monkey_patch.Spec.from_target(target_module.Top) == top_spec
        assert monkey_patch.Spec.from_target(target_module.Top.Nested) == nested_spec
        assert (
            monkey_patch.Spec.from_target(target_module.Top.Nested.DoubleNested)
            == double_nested_spec
        )
