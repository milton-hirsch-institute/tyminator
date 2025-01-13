# Copyright 2023-2025 The Milton Hirsch Institute, B.V.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import functools
import importlib
import operator
import sys
import types
import typing
from typing import Any
from typing import Optional


@dataclasses.dataclass(frozen=True, order=True)
class Spec:
    module_name: str
    qualified_name: str

    @functools.cached_property
    def name(self) -> str:
        return self.__qualified_name_tuple[-1]

    @functools.cached_property
    def __qualified_name_tuple(self) -> tuple[str]:
        return tuple(self.qualified_name.split("."))

    @functools.cached_property
    def parent_qualified_name(self) -> Optional[str]:
        parent_name = self.__qualified_name_tuple[:-1]
        return ".".join(parent_name) if parent_name else None

    @functools.cached_property
    def __getter(self) -> operator.attrgetter:
        return operator.attrgetter(self.qualified_name)

    def get_module(self) -> types.ModuleType:
        try:
            return sys.modules[self.module_name]
        except KeyError:
            return importlib.import_module(self.module_name)

    def get_obj(self) -> Any:
        return self.__getter(self.get_module())

    @classmethod
    def from_target(cls, target: Any) -> "Spec":
        return cls(target.__module__, target.__qualname__)


@dataclasses.dataclass(frozen=True)
class Patch:

    original_obj: Any
    spec: Spec

    def install(self, obj: Any) -> None:
        module = self.spec.get_module()
        parent_name = self.spec.parent_qualified_name
        if parent_name:
            parent_getter = operator.attrgetter(parent_name)
            parent = parent_getter(module)
        else:
            parent = module
        setattr(parent, self.spec.name, obj)

    def restore(self) -> None:
        self.install(self.original_obj)

    @classmethod
    def from_spec(cls, spec: Spec) -> "Patch":
        return cls(spec.get_obj(), spec)

    @classmethod
    def from_target(cls, target: Any) -> "Patch":
        spec = Spec.from_target(target)
        return cls.from_spec(spec)

    @classmethod
    def from_any(cls, any: Any) -> "Patch":
        if isinstance(any, Spec):
            return cls.from_spec(any)
        else:
            return cls.from_target(any)


@typing.final
class PatchSet:
    __patches: dict[str, Patch]
    __initialized = False

    def __init__(self, **kwargs):
        self.__patches = {}
        for name, value in kwargs.items():
            self.__patches[name] = Patch.from_any(value)
        self.__initialized = True

    def install(self, **kwargs):
        missing_patches = self.__patches.keys() - kwargs.keys()
        if missing_patches:
            missing_patches_list = ", ".join(sorted(missing_patches))
            raise ValueError(f"missing patches: {missing_patches_list}")

        unexpected_patches = kwargs.keys() - self.__patches.keys()
        if unexpected_patches:
            extra_patches_list = ", ".join(sorted(unexpected_patches))
            raise ValueError(f"unexpected patches: {extra_patches_list}")

        for name, patch in self.__patches.items():
            patch.install(kwargs[name])

    def restore(self):
        for patch in self.__patches.values():
            patch.restore()

    def __getattr__(self, item):
        try:
            patch = self.__patches[item]
        except KeyError:
            return getattr(super(), item)
        else:
            return patch.original_obj

    def __setattr__(self, key, value):
        if self.__initialized:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {key!r}"
            )
        else:
            object.__setattr__(self, key, value)


__all__ = ("Patch", "PatchSet", "Spec")
