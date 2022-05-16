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


@pytest.fixture
def top_patch(top_spec):
    return monkey_patch.Patch.from_spec(top_spec)


@pytest.fixture
def nested_patch(nested_spec):
    return monkey_patch.Patch.from_spec(nested_spec)


@pytest.fixture
def double_nested_patch(double_nested_spec):
    return monkey_patch.Patch.from_spec(double_nested_spec)


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


class TestPatch:
    class TestInstallAndRestore:
        @staticmethod
        def test_top(top_patch):
            new_object = object()
            try:
                top_patch.install(new_object)
                assert target_module.Top is new_object
            finally:
                top_patch.restore()
                assert target_module.Top is top_patch.original_obj

        @staticmethod
        def test_nested(nested_patch):
            new_object = object()
            try:
                nested_patch.install(new_object)
                assert target_module.Top.Nested is new_object
            finally:
                nested_patch.restore()
                assert target_module.Top.Nested is nested_patch.original_obj

        @staticmethod
        def test_double_nested(double_nested_patch):
            new_object = object()
            try:
                double_nested_patch.install(new_object)
                assert target_module.Top.Nested.DoubleNested is new_object
            finally:
                double_nested_patch.restore()
                assert (
                    target_module.Top.Nested.DoubleNested
                    is double_nested_patch.original_obj
                )

    @staticmethod
    def test_from_spec(top_spec, nested_spec, double_nested_spec):
        top_patch = monkey_patch.Patch.from_spec(top_spec)
        nested_patch = monkey_patch.Patch.from_spec(nested_spec)
        double_nested_patch = monkey_patch.Patch.from_spec(double_nested_spec)

        assert top_patch.spec is top_spec
        assert nested_patch.spec is nested_spec
        assert double_nested_patch.spec is double_nested_spec

        assert top_patch.original_obj is target_module.Top
        assert nested_patch.original_obj is target_module.Top.Nested
        assert double_nested_patch.original_obj is target_module.Top.Nested.DoubleNested

    @staticmethod
    def test_from_target(top_patch, nested_patch, double_nested_patch):
        assert monkey_patch.Patch.from_target(target_module.Top) == top_patch
        assert monkey_patch.Patch.from_target(target_module.Top.Nested) == nested_patch
        assert (
            monkey_patch.Patch.from_target(target_module.Top.Nested.DoubleNested)
            == double_nested_patch
        )
