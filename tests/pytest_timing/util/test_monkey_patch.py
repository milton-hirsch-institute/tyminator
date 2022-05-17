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
def object1_spec():
    return monkey_patch.Spec(target_module.__name__, "object1")


@pytest.fixture
def object2_spec():
    return monkey_patch.Spec(target_module.__name__, "object2")


@pytest.fixture
def object3_spec():
    return monkey_patch.Spec(target_module.__name__, "object3")


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
def patch_set(object1_spec, object2_spec, object3_spec):
    return monkey_patch.PatchSet(
        object1=object1_spec,
        object2=object2_spec,
        object3=object3_spec,
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
            assert patch_set.object1 is target_module.object1
            assert patch_set.object2 is target_module.object2
            assert patch_set.object3 is target_module.object3

        @staticmethod
        def test_from_target():
            patch_set = monkey_patch.PatchSet(
                object1=target_module.object1,
                object2=target_module.object2,
                object3=target_module.object3,
            )
            assert patch_set.object1 == target_module.object1
            assert patch_set.object2 == target_module.object2
            assert patch_set.object3 == target_module.object3

    class TestAttributes:
        @staticmethod
        def test_immutable():
            patch_set = monkey_patch.PatchSet()
            with pytest.raises(
                AttributeError, match=r"'PatchSet' object has no attribute 'time_func'"
            ):
                patch_set.time_func = target_module.object1

        @staticmethod
        def test_no_such_patch(patch_set):
            with pytest.raises(AttributeError):
                patch_set.no_such_patch

    class TestInstall:
        @staticmethod
        def test_missing_patches(patch_set):
            with pytest.raises(
                ValueError, match=r"^missing patches: object2, object3$"
            ):
                patch_set.install(object1=object())
            assert target_module.object1 is patch_set.object1
            assert target_module.object2 is patch_set.object2
            assert target_module.object3 is patch_set.object3

        @staticmethod
        def test_unexpected_patches(patch_set):
            with pytest.raises(
                ValueError, match=r"unexpected patches: unknown1, unknown2"
            ):
                patch_set.install(
                    object1=object(),
                    object2=object(),
                    object3=object(),
                    unknown1=object(),
                    unknown2=object(),
                )
            assert target_module.object1 is patch_set.object1
            assert target_module.object2 is patch_set.object2
            assert target_module.object3 is patch_set.object3

        @staticmethod
        def test_install(patch_set):
            object1 = object()
            object2 = object()
            object3 = object()
            patch_set.install(object1=object1, object2=object2, object3=object3)
            assert target_module.object1 is object1
            assert target_module.object2 is object2
            assert target_module.object3 is object3

    @staticmethod
    def test_restore(patch_set):
        target_module.object1 = object()
        target_module.object2 = object()
        target_module.object3 = object()
        patch_set.restore()
        assert target_module.object1 is patch_set.object1
        assert target_module.object2 is patch_set.object2
        assert target_module.object3 is patch_set.object3
