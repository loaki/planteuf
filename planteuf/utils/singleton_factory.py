from __future__ import annotations

import re
from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from planteuf.utils.sanitizer import Sanitizer


T = TypeVar("T")
Creatable = TypeVar("Creatable")


@dataclass
class NamedCreatable(Generic[T]):
    data_type: T
    name: Optional[str] = None

    def __hash__(self) -> int:
        return hash((self.data_type, self.name))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{repr(self.data_type)}{('#' + self.name) if self.name else ''}]"


def _to_named_creatable(
    data_type: Union[NamedCreatable[T], T],
) -> NamedCreatable[T]:
    if not isinstance(data_type, NamedCreatable):
        return NamedCreatable(data_type=data_type, name=None)
    return data_type


creator_repr_sanitizer = Sanitizer(
    sanitize_keys={re.compile(".*")},
    fn=lambda key, value: repr(value) if isinstance(value, Creator) else repr(f"**SANITIZED {type(value)}**"),
)


class Creator(Generic[Creatable]):
    _data_type: NamedCreatable[Type[Creatable]]
    _args: Tuple[Any, ...]
    _kwargs: Dict[str, Any]

    def __init__(
        self,
        data_type: Union[NamedCreatable[Type[Creatable]], Type[Creatable]],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ):
        if not isinstance(data_type, NamedCreatable):
            data_type = NamedCreatable(data_type=data_type, name=None)
        self._data_type = data_type
        self._args = args
        self._kwargs = kwargs

    def get_type(self) -> NamedCreatable[Type[Creatable]]:
        return self._data_type

    def get_args(self) -> Tuple[Any, ...]:
        return self._args

    def get_kwargs(self) -> Dict[str, Any]:
        return self._kwargs

    def __repr__(self) -> str:
        all_args = list(map(repr, self._args))
        all_args += list(map(lambda kw: f"{kw[0]}={kw[1]}", creator_repr_sanitizer.sanitize(self._kwargs).items()))
        return f"{self.__class__.__name__}[{self._data_type.data_type.__name__}]({', '.join(all_args)})"


class ICreatorVisitor(ABC):
    @abstractmethod
    def visit(self, named: NamedCreatable[Any], creator: Creator[Any]) -> None: ...


class SingletonFactory:
    _creators: Dict[NamedCreatable[Any], Creator[Any]] = {}
    _cache: Dict[NamedCreatable[Any], Any] = {}
    _instance: SingletonFactory

    def __new__(cls, *args: Any, **kwargs: Any) -> SingletonFactory:
        try:
            return cls._instance
        except AttributeError:
            return object.__new__(cls, *args, **kwargs)

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._creators = {}
        self._cache = {}

    @classmethod
    def instance(cls) -> SingletonFactory:
        try:
            return cls._instance
        except AttributeError:
            cls._instance = SingletonFactory()
            return cls._instance

    def register_creator(
        self, data_type: Union[NamedCreatable[Type[Creatable]], Type[Creatable]], *args: Any, **kwargs: Any
    ) -> Creator[Creatable]:
        named = _to_named_creatable(data_type=data_type)
        if named in self._cache:
            del self._cache[named]
        self._remove_arg_dependency_from_cache(data_type=named)
        creator = Creator(data_type=named, args=args, kwargs=kwargs)
        self._creators[named] = creator
        return creator

    def get_creator(
        self, data_type: Union[NamedCreatable[Type[Creatable]], Type[Creatable]]
    ) -> Optional[Creator[Creatable]]:
        named = _to_named_creatable(data_type=data_type)
        if named not in self._creators:
            if named.name is None:
                eligible: List[NamedCreatable[Type[Creatable]]] = []
                for named_data_type in self._creators.keys():
                    if named_data_type.data_type == named.data_type or self._is_subclass(
                        named.data_type, named_data_type.data_type
                    ):
                        eligible.append(cast(NamedCreatable[Type[Creatable]], named_data_type))
                if not eligible:
                    return None
                if len(eligible) != 1:
                    names = ", ".join([named.name or f"[unnamed-{named.data_type}]" for named in eligible])
                    raise SingletonFactoryException(
                        f"Multiple creatable of type {named.data_type} available, "
                        + f"please use one of the following available names: {names} or use a more specific type"
                    )
                named = eligible[0]
            else:
                return None
        return self._creators[named]

    def delete(self, data_type: Union[NamedCreatable[Type[Creatable]], Type[Creatable]]) -> None:
        named = _to_named_creatable(data_type=data_type)
        if named in self._creators:
            del self._creators[named]
        if named in self._cache:
            del self._cache[named]

    def get_named_creatables(
        self, data_type: Type[Creatable], with_name: bool = False
    ) -> List[NamedCreatable[Type[Creatable]]]:
        return list(
            filter(
                lambda named: (named.name or not with_name)
                and (data_type == named.data_type or self._is_subclass(data_type, named.data_type)),
                self._creators.keys(),
            )
        )

    def _remove_arg_dependency_from_cache(self, data_type: NamedCreatable[Type[Creatable]]) -> None:
        for creator in self._creators.values():
            for creator_arg in creator.get_args():
                if (
                    isinstance(creator_arg, Creator)
                    and creator_arg.get_type() == data_type
                    and creator.get_type() in self._cache
                ):
                    del self._cache[creator.get_type()]
            for _, creator_kwarg_value in creator.get_kwargs().items():
                if (
                    isinstance(creator_kwarg_value, Creator)
                    and creator_kwarg_value.get_type() == data_type
                    and creator.get_type() in self._cache
                ):
                    del self._cache[creator.get_type()]

    def get_all(self, data_type: Type[Creatable]) -> Set[Creatable]:
        named = _to_named_creatable(data_type=data_type)
        eligible: Set[Creatable] = set()
        for named_data_type in self._creators.keys():
            if named_data_type.data_type == named.data_type or self._is_subclass(
                named.data_type, named_data_type.data_type
            ):
                eligible.add(self.get(cast(NamedCreatable[Type[Creatable]], named_data_type)))
        return eligible

    def get(self, data_type: Union[NamedCreatable[Type[Creatable]], Type[Creatable]]) -> Creatable:
        named = _to_named_creatable(data_type=data_type)
        if named not in self._creators:
            if named.name is None:
                eligible: List[NamedCreatable[Type[Creatable]]] = []
                for named_data_type in self._creators.keys():
                    if named_data_type.data_type == named.data_type or self._is_subclass(
                        named.data_type, named_data_type.data_type
                    ):
                        eligible.append(cast(NamedCreatable[Type[Creatable]], named_data_type))
                if not eligible:
                    raise SingletonFactoryException(f"{named} not registered")
                if len(eligible) != 1:
                    names = ", ".join([named.name or f"[unnamed-{named.data_type}]" for named in eligible])
                    raise SingletonFactoryException(
                        f"Multiple creatable of type {named.data_type} available, "
                        + f"please use one of the following available names: {names} or use a more specific type"
                    )
                named = eligible[0]
            else:
                raise SingletonFactoryException(f"{named} not registered")
        if named not in self._cache:
            creator = self._creators[named]
            try:
                self._cache[named] = creator.get_type().data_type(
                    *self._get_args(*creator.get_args()),
                    **self._get_kwargs(**creator.get_kwargs()),
                )
            except Exception as e:
                raise SingletonFactoryException(f"Unable to instantiate {creator}") from e
        return cast(Creatable, self._cache[named])

    @classmethod
    def _is_subclass(cls, child: Type[Creatable], parent: Type[Creatable]) -> bool:
        if not parent.__bases__:
            return False
        for base in parent.__bases__:
            if child == base or cls._is_subclass(child, base):
                return True
        return False

    def _get_args(self, *args: Any) -> List[Any]:
        new_args = []
        for arg in args:
            new_args.append(self._get_arg(arg))
        return new_args

    def _get_kwargs(self, **kwargs: Any) -> Dict[str, Any]:
        new_kwargs = {}
        for key, arg in kwargs.items():
            new_kwargs[key] = self._get_arg(arg)
        return new_kwargs

    def _get_arg(self, arg: Any) -> Any:
        if isinstance(arg, Creator):
            arg = self.get(arg.get_type())
        elif isinstance(arg, list):
            arg = [self._get_arg(item) for item in arg]
        elif isinstance(arg, set):
            arg = {self._get_arg(item) for item in arg}
        elif isinstance(arg, dict):
            arg = {key: self._get_arg(item) for key, item in arg.items()}
        return arg

    def visit(self, visitor: ICreatorVisitor) -> None:
        for named, creator in self._creators.items():
            visitor.visit(named=named, creator=creator)


class SingletonFactoryException(Exception):
    pass
