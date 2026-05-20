# Copyright (c) Microsoft Corporation. All rights reserved.

"""Trigger callback payload types for Connector Namespace integration."""

import json
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, List, Optional, Union

T = TypeVar("T")


@dataclass
class TriggerCallbackBody(Generic[T]):
    """
    Inner body of the Connector Namespace trigger callback.

    Deserialization is handled by :meth:`from_dict` which accepts both
    batch (``{"value": [...]}``) and single-item (``{...item...}``) JSON shapes.
    """

    value: Optional[List[T]] = None
    """
    The list of trigger items delivered by the connector trigger.
    Contains all items regardless of whether the callback arrived in batch or
    single-item shape. May be None when the source payload contained an explicit
    "value": null property (or a null body), so consumers should null-check
    before iterating.
    """

    @classmethod
    def from_dict(
        cls,
        data: Optional[dict],
        item_factory: Optional[Callable[[dict], T]] = None,
    ) -> "TriggerCallbackBody[T]":
        """Parse a dictionary into a TriggerCallbackBody, handling both batch
        and single-item shapes.

        The Connector Namespace delivers callbacks in two shapes depending on
        the trigger configuration's splitOn setting:

        - Batch (splitOn disabled): ``{"value": [...items...]}``
        - Single-item (splitOn enabled): ``{...item properties...}``

        This method normalizes both into a list in the ``value`` field.

        Args:
            data: The body dictionary from the trigger callback payload.
            item_factory: Optional callable to convert each raw dict item into
                a typed object T. If None, items are stored as raw dicts.

        Returns:
            A TriggerCallbackBody instance with value always as a list.
        """
        if data is None:
            return cls(value=None)

        # Determine if this is the batch shape: a dict whose sole property
        # is "value" (list or null). The Connector Namespace batch envelope
        # always carries exactly one property; item types always carry
        # multiple fields.
        value_element = data.get("value")
        is_batch_shape = (
            "value" in data
            and len(data) == 1
            and (isinstance(value_element, list) or value_element is None)
        )

        if is_batch_shape:
            # Batch shape: {"value": [...items...]} or {"value": null}
            if value_element is None:
                return cls(value=None)
            items = [
                item_factory(item) if item_factory and isinstance(item, dict) else item
                for item in value_element
            ]
            return cls(value=items)

        # Single-item shape: {...item properties...} — wrap in a one-element list.
        single_item: T = item_factory(data) if item_factory else data  # type: ignore[assignment]
        return cls(value=[single_item])


@dataclass
class TriggerCallbackPayload(Generic[T]):
    """
    Envelope type for Connector Namespace trigger callback payloads.

    The Connector Namespace delivers callbacks in two shapes depending on the
    trigger configuration's splitOn setting:

    - Batch (splitOn disabled): ``{"body": {"value": [...items...]}}``
    - Single-item (splitOn enabled): ``{"body": {...item...}}``

    Use :meth:`from_json` or :meth:`from_dict` to parse either shape
    transparently — the result always normalizes items into
    :attr:`TriggerCallbackBody.value` as a list.

    Type parameter T is the connector-specific trigger item type
    (e.g., GraphClientReceiveMessage for Office 365 email triggers).
    """

    body: Optional[TriggerCallbackBody[T]] = None
    """The body envelope containing the trigger items."""

    @classmethod
    def from_json(
        cls,
        payload: Union[str, dict],
        item_factory: Optional[Callable[[dict], T]] = None,
    ) -> "TriggerCallbackPayload[T]":
        """Parse a JSON string or dict into a TriggerCallbackPayload.

        Handles both batch and single-item shapes transparently.

        Args:
            payload: A JSON string or dictionary containing the trigger payload.
                Expected structure: ``{"body": {"value": [...]}}`` (batch) or
                ``{"body": {...item...}}`` (single-item).
            item_factory: Optional callable to convert each raw dict item into
                a typed object T. If None, items are stored as raw dicts.

        Returns:
            A TriggerCallbackPayload instance.

        Raises:
            ValueError: If the payload is a string that cannot be parsed as JSON.
        """
        if hasattr(payload, "value"):
            # Datum-like wrapper from the worker extension converter layer
            payload = payload.value

        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON payload: {e}.") from e
        else:
            data = payload

        return cls.from_dict(data, item_factory=item_factory)

    @classmethod
    def from_dict(
        cls,
        data: Optional[dict],
        item_factory: Optional[Callable[[dict], T]] = None,
    ) -> "TriggerCallbackPayload[T]":
        """Parse a dictionary into a TriggerCallbackPayload.

        Args:
            data: The payload dictionary.
            item_factory: Optional callable to convert each raw dict item into
                a typed object T.

        Returns:
            A TriggerCallbackPayload instance.
        """
        if data is None:
            return cls(body=None)

        body_data = data.get("body")
        if body_data is None:
            return cls(body=None)

        body = TriggerCallbackBody.from_dict(body_data, item_factory=item_factory)
        return cls(body=body)
