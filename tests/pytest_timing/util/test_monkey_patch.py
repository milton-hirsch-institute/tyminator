import importlib
import sys

import pytest

from pytest_timing.util import monkey_patch
from tests.pytest_timing.util import target_module


@pytest.fixture(autouse=True)
def reloaded_target_module():
    try:
        yield
    finally:
        importlib.reload(target_module)


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
def time_func_spec():
    return monkey_patch.Spec(target_module.__name__, "time_func")


@pytest.fixture
def sleep_func_spec():
    return monkey_patch.Spec(target_module.__name__, "sleep_func")


@pytest.fixture
def async_sleep_func_spec():
    return monkey_patch.Spec(target_module.__name__, "async_sleep_func")


@pytest.fixture
def top_patch(top_spec):
    return monkey_patch.Patch.from_spec(top_spec)


@pytest.fixture
def nested_patch(nested_spec):
    return monkey_patch.Patch.from_spec(nested_spec)


@pytest.fixture
def double_nested_patch(double_nested_spec):
    return monkey_patch.Patch.from_spec(double_nested_spec)


@pytest.fixture
def patch_set(time_func_spec, sleep_func_spec, async_sleep_func_spec):
    return monkey_patch.PatchSet(
        time=time_func_spec,
        sleep=sleep_func_spec,
        async_sleep=async_sleep_func_spec,
    )


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

    @staticmethod
    def test_from_any(
        top_spec,
        nested_spec,
        double_nested_spec,
        top_patch,
        nested_patch,
        double_nested_patch,
    ):
        assert monkey_patch.Patch.from_any(top_spec) == top_patch
        assert monkey_patch.Patch.from_any(nested_spec) == nested_patch
        assert monkey_patch.Patch.from_any(double_nested_spec) == double_nested_patch

        assert monkey_patch.Patch.from_any(target_module.Top) == top_patch
        assert monkey_patch.Patch.from_any(target_module.Top.Nested) == nested_patch
        assert (
            monkey_patch.Patch.from_any(target_module.Top.Nested.DoubleNested)
            == double_nested_patch
        )


class TestPatchSet:
    class TestConstructor:
        @staticmethod
        def test_from_spec(patch_set):
            assert patch_set.time == target_module.time_func
            assert patch_set.sleep == target_module.sleep_func
            assert patch_set.async_sleep == target_module.async_sleep_func

        @staticmethod
        def test_from_target():
            patch_set = monkey_patch.PatchSet(
                time=target_module.time_func,
                sleep=target_module.sleep_func,
                async_sleep=target_module.async_sleep_func,
            )
            assert patch_set.time == target_module.time_func
            assert patch_set.sleep == target_module.sleep_func
            assert patch_set.async_sleep == target_module.async_sleep_func

    class TestAttributes:
        @staticmethod
        def test_immutable():
            patch_set = monkey_patch.PatchSet()
            with pytest.raises(
                AttributeError, match=r"'PatchSet' object has no attribute 'time_func'"
            ):
                patch_set.time_func = target_module.time_func

        @staticmethod
        def test_no_such_patch(patch_set):
            with pytest.raises(AttributeError):
                patch_set.no_such_patch

    class TestInstall:
        @staticmethod
        def test_missing_patches(patch_set):
            with pytest.raises(
                ValueError, match=r"^missing patches: async_sleep, sleep$"
            ):
                patch_set.install(time=object())
            assert target_module.time_func is patch_set.time
            assert target_module.sleep_func is patch_set.sleep
            assert target_module.async_sleep_func is patch_set.async_sleep

        @staticmethod
        def test_unexpected_patches(patch_set):
            with pytest.raises(
                ValueError, match=r"unexpected patches: unknown1, unknown2"
            ):
                patch_set.install(
                    time=object(),
                    sleep=object(),
                    async_sleep=object(),
                    unknown1=object(),
                    unknown2=object(),
                )
            assert target_module.time_func is patch_set.time
            assert target_module.sleep_func is patch_set.sleep
            assert target_module.async_sleep_func is patch_set.async_sleep

        @staticmethod
        def test_install(patch_set):
            time = object()
            sleep = object()
            async_sleep = object()
            patch_set.install(time=time, sleep=sleep, async_sleep=async_sleep)
            assert target_module.time_func is time
            assert target_module.sleep_func is sleep
            assert target_module.async_sleep_func is async_sleep

    @staticmethod
    def test_restore(patch_set):
        target_module.time_func = "time"
        target_module.sleep_func = "sleep"
        target_module.async_sleep_func = "async_sleep"
        patch_set.restore()
        assert target_module.time_func is patch_set.time
        assert target_module.sleep_func is patch_set.sleep
        assert target_module.async_sleep_func is patch_set.async_sleep
