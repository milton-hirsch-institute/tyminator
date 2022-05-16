import dataclasses
import functools
import importlib
import operator
import sys
from typing import Any
from typing import Callable
from typing import Optional


@dataclasses.dataclass(frozen=True, order=True)
class Spec:
    module_name: str
    qualified_name: str

    @functools.cached_property
    def name(self):
        return self.__qualified_name_tuple[-1]

    @functools.cached_property
    def __qualified_name_tuple(self) -> tuple[str]:
        return tuple(self.qualified_name.split("."))

    @functools.cached_property
    def parent_qualified_name(self) -> Optional[str]:
        parent_name = self.__qualified_name_tuple[:-1]
        return ".".join(parent_name) if parent_name else None

    @functools.cached_property
    def __getter(self):
        return operator.attrgetter(self.qualified_name)

    def get_module(self):
        try:
            return sys.modules[self.module_name]
        except KeyError:
            return importlib.import_module(self.module_name)

    def get_obj(self):
        return self.__getter(self.get_module())

    @classmethod
    def from_target(cls, target: Callable) -> "Spec":
        return cls(target.__module__, target.__qualname__)


@dataclasses.dataclass(frozen=True)
class Patch:

    original_obj: Any
    spec: Spec

    def install(self, obj: Any):
        module = self.spec.get_module()
        parent_name = self.spec.parent_qualified_name
        if parent_name:
            parent_getter = operator.attrgetter(parent_name)
            parent = parent_getter(module)
        else:
            parent = module
        setattr(parent, self.spec.name, obj)

    def restore(self):
        self.install(self.original_obj)

    @classmethod
    def from_spec(cls, spec: Spec):
        return cls(spec.get_obj(), spec)


__all__ = ("Patch", "Spec")
