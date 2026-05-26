# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Trigger callback payload types for Connector Namespace integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Optional, TypeVar, cast

T = TypeVar("T")


def _is_batch_shape(data: dict[str, Any]) -> bool:
    """
    Determine if the given dictionary represents a batch shape.

    The batch shape has a SOLE property named "value" that is either a list or None.
    A single-item shape is anything else (multiple properties, or a "value" that is
    not a list/None).

    Args:
        data: The dictionary to inspect.

    Returns:
        True if this is a batch shape, False if it's a single-item shape.
    """
    if len(data) != 1:
        return False

    if "value" not in data:
        return False

    value = data["value"]
    return value is None or isinstance(value, list)


@dataclass
class TriggerCallbackBody(Generic[T]):
    """
    Inner body of the Connector Namespace trigger callback, containing the
    array of trigger items.

    Deserialization handles both batch and single-item JSON shapes:

    - Batch (splitOn disabled): ``{"value": [...items...]}``
    - Single-item (splitOn enabled): ``{...item properties...}``

    Both shapes are normalized into the ``value`` list.
    """

    value: Optional[List[T]] = None
    """
    The list of trigger items delivered by the connector trigger.
    Contains all items regardless of whether the callback arrived in batch or
    single-item shape. May be None when the source payload contained an explicit
    ``"value": null`` property (or a null body), so consumers should null-check
    before iterating.
    """

    @classmethod
    def from_dict(
        cls,
        data: Optional[dict[str, Any]],
        item_parser: Optional[Callable[[dict[str, Any]], T]] = None,
    ) -> Optional[TriggerCallbackBody[T]]:
        """
        Parse a dictionary into a TriggerCallbackBody, handling both batch and
        single-item shapes.

        The Connector Namespace delivers trigger callbacks in two shapes depending
        on the trigger configuration's splitOn setting:

        - Batch (splitOn disabled): ``{"value": [...items...]}``
        - Single-item (splitOn enabled): ``{...item properties...}``

        This method transparently normalizes both shapes into ``value`` as a list.

        Args:
            data: The dictionary to parse, or None.
            item_parser: Optional callable to convert each item dict to type T.
                If not provided, items are returned as-is (dict).

        Returns:
            A TriggerCallbackBody instance, or None if data is None.

        Example:
            >>> # Batch shape
            >>> batch_data = {"value": [{"id": "1"}, {"id": "2"}]}
            >>> body = TriggerCallbackBody.from_dict(batch_data)
            >>> len(body.value)
            2

            >>> # Single-item shape
            >>> single_data = {"id": "1", "subject": "Test"}
            >>> body = TriggerCallbackBody.from_dict(single_data)
            >>> len(body.value)
            1
        """
        if data is None:
            return None

        if _is_batch_shape(data):
            # Batch shape: {"value": [...items...]} or {"value": null}
            raw_items = data.get("value")
            if raw_items is None:
                return cls(value=None)

            if item_parser is not None:
                items: List[T] = [item_parser(item) for item in raw_items]
            else:
                items = cast(List[T], list(raw_items))

            return cls(value=items)

        # Single-item shape: {...item properties...} — wrap in a one-element list.
        if item_parser is not None:
            single_item: T = item_parser(data)
        else:
            single_item = cast(T, data)

        return cls(value=[single_item])


@dataclass
class TriggerCallbackPayload(Generic[T]):
    """
    Envelope type for Connector Namespace trigger callback payloads.

    The Connector Namespace delivers callbacks in two shapes depending on the
    trigger configuration's splitOn setting:

    - Batch (splitOn disabled): ``{"body": {"value": [...items...]}}``
    - Single-item (splitOn enabled): ``{"body": {...item...}}``

    Use the :meth:`from_dict` factory method to parse payloads that handles
    both shapes transparently, always normalizing into ``body.value`` as a list.

    Type parameter T is the connector-specific trigger item type
    (e.g., GraphClientReceiveMessage for Office 365 email triggers).
    """

    body: Optional[TriggerCallbackBody[T]] = None
    """The body envelope containing the trigger items."""

    @classmethod
    def from_dict(
        cls,
        data: Optional[dict[str, Any]],
        item_parser: Optional[Callable[[dict[str, Any]], T]] = None,
    ) -> Optional[TriggerCallbackPayload[T]]:
        """
        Parse a dictionary into a TriggerCallbackPayload, handling both batch
        and single-item shapes.

        Args:
            data: The dictionary to parse (typically from JSON), or None.
            item_parser: Optional callable to convert each item dict to type T.
                If not provided, items are returned as-is (dict).

        Returns:
            A TriggerCallbackPayload instance, or None if data is None.

        Example:
            >>> import json
            >>> # Batch shape payload
            >>> batch_json = '{"body": {"value": [{"id": "1"}]}}'
            >>> payload = TriggerCallbackPayload.from_dict(json.loads(batch_json))
            >>> len(payload.body.value)
            1

            >>> # Single-item shape payload
            >>> single_json = '{"body": {"id": "1", "subject": "Test"}}'
            >>> payload = TriggerCallbackPayload.from_dict(json.loads(single_json))
            >>> len(payload.body.value)
            1
        """
        if data is None:
            return None

        body_data = data.get("body")
        body = TriggerCallbackBody.from_dict(body_data, item_parser)

        return cls(body=body)
