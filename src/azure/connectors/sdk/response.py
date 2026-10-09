# Copyright (c) Microsoft Corporation. All rights reserved.

"""Public response contracts for connector request hooks."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping, TypeAlias


@dataclass(frozen=True)
class ConnectorResponseSnapshot:
    """Immutable snapshot of a completed connector HTTP response."""

    status: int
    headers: Mapping[str, str]
    text: str
    content: bytes

    def __post_init__(self) -> None:
        """Freeze a defensive copy of the response headers."""
        object.__setattr__(
            self,
            "headers",
            MappingProxyType(dict(self.headers)),
        )


ConnectorResponseHook: TypeAlias = Callable[
    [ConnectorResponseSnapshot, Mapping[str, str]],
    None,
]
"""Callback invoked after a connector HTTP response is received."""

__all__ = ["ConnectorResponseHook", "ConnectorResponseSnapshot"]
