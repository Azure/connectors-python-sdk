# Copyright (c) Microsoft Corporation. All rights reserved.

"""Trigger callback payload types for AI Gateway integration."""

from dataclasses import dataclass
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


@dataclass
class TriggerCallbackBody(Generic[T]):
    """
    Inner body of the AI Gateway trigger callback, containing the
    array of trigger items.
    """

    value: Optional[List[T]] = None
    """
    The list of trigger items delivered by the connector trigger.
    Split-on is not supported — consumers must iterate this array.
    """


@dataclass
class TriggerCallbackPayload(Generic[T]):
    """
    Envelope type for AI Gateway trigger callback payloads.

    The AI Gateway wraps triggerBody() in a {"body":{"value":[...]}}
    structure.

    Type parameter T is the connector-specific trigger item type
    (e.g., GraphClientReceiveMessage for Office 365 email triggers).
    """

    body: Optional[TriggerCallbackBody[T]] = None
    """The body envelope containing the trigger items."""
