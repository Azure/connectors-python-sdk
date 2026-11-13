# Copyright (c) Microsoft Corporation. All rights reserved.

"""Public response contracts for connector requests and paginated results."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, AsyncIterator, Callable, Generic, Mapping, Optional, TypeAlias, TypeVar


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


ItemT = TypeVar("ItemT")


class ConnectorPage(AsyncIterator[ItemT], Generic[ItemT]):
    """One iterable page retaining both its parsed model and raw HTTP response."""

    def __init__(
        self,
        items_iterator: AsyncIterator[ItemT],
        *,
        page_model: Any,
        raw_response: ConnectorResponseSnapshot,
        continuation_token: Optional[str] = None,
    ) -> None:
        """Capture the page alongside the iterator of its individual items."""
        self._items_iterator = items_iterator
        self.page_model = page_model
        self.raw_response = raw_response
        self.continuation_token = continuation_token

    def __aiter__(self) -> ConnectorPage[ItemT]:
        """Iterate the page without discarding its raw or parsed envelope."""
        return self

    async def __anext__(self) -> ItemT:
        """Yield the next item from the wrapped page iterator."""
        return await self._items_iterator.__anext__()


ConnectorResponseHook: TypeAlias = Callable[
    [ConnectorResponseSnapshot, Mapping[str, str]],
    None,
]
"""Callback invoked after a connector HTTP response is received."""

__all__ = ["ConnectorPage", "ConnectorResponseHook", "ConnectorResponseSnapshot"]
