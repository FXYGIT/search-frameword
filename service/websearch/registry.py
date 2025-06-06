# service/websearch/registry.py

from typing import Type, Dict
from service.websearch.base import BaseSearchEngine


_engine_registry: Dict[str, Type[BaseSearchEngine]] = {}


def register_engine(name: str):
    """
    装饰器注册搜索引擎类
    """
    def decorator(cls: Type[BaseSearchEngine]):
        _engine_registry[name] = cls
        return cls
    return decorator


def get_engine(name: str, *args, **kwargs) -> BaseSearchEngine:
    """
    根据名字动态返回对应搜索引擎实例
    """
    engine_cls = _engine_registry.get(name)
    if not engine_cls:
        raise ValueError(f"Search engine '{name}' is not registered.")
    return engine_cls(*args, **kwargs)
