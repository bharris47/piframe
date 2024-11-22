import importlib
from typing import Generic, TypeVar, Type

from pydantic import BaseModel

T = TypeVar("T")

class ModuleDefinition(BaseModel, Generic[T]):
    """A definition that can be used to initialize a class"""
    class_path: str
    args: dict

def load_class(definition: ModuleDefinition[T]) -> Type[T]:
    module_path, class_name = definition.class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
