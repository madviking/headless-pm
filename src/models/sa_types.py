from __future__ import annotations

from enum import Enum as PyEnum
from typing import Any, Optional, Type

from sqlalchemy.types import String, TypeDecorator


class EnumValueString(TypeDecorator):
    """
    Stores a Python Enum as its `.value` in the database (string).

    Compatibility:
    - Accepts Enum instances, enum `.value` strings, and legacy enum `.name` strings.
    - On read, converts DB strings back into Enum members (by value, then by name).
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_cls: Type[PyEnum], *, length: int = 50) -> None:
        self._enum_cls = enum_cls
        super().__init__(length=length)

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None

        store_enum_name = getattr(dialect, "name", "").lower() == "mysql"

        if isinstance(value, self._enum_cls):
            return str(value.name) if store_enum_name else str(value.value)

        if isinstance(value, str):
            # Allow binding either the enum value (preferred) or legacy enum name.
            try:
                member = self._enum_cls(value)
                return str(member.name) if store_enum_name else str(member.value)
            except Exception:
                try:
                    member = self._enum_cls[value]
                    return str(member.name) if store_enum_name else str(member.value)
                except Exception as e:
                    raise ValueError(
                        f"Invalid value '{value}' for enum {self._enum_cls.__name__}"
                    ) from e

        raise TypeError(
            f"Expected {self._enum_cls.__name__} or str, got {type(value).__name__}"
        )

    def process_result_value(self, value: Any, dialect: Any) -> Optional[PyEnum]:
        if value is None:
            return None

        if isinstance(value, self._enum_cls):
            return value

        if isinstance(value, str):
            try:
                return self._enum_cls(value)
            except Exception:
                try:
                    return self._enum_cls[value]
                except Exception as e:
                    raise ValueError(
                        f"Invalid DB value '{value}' for enum {self._enum_cls.__name__}"
                    ) from e

        raise TypeError(
            f"Expected DB value str for enum {self._enum_cls.__name__}, got {type(value).__name__}"
        )
