# Copyright (c) Microsoft Corporation. All rights reserved.

"""Configuration options for connector clients."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConnectorClientOptions:
    """Configuration options for connector clients."""

    base_uri: Optional[str] = None
    """The base URI for the connector endpoint."""

    max_retry_attempts: int = 3
    """The maximum number of retry attempts."""

    timeout_seconds: float = 30.0
    """The timeout for HTTP requests in seconds."""

    use_exponential_backoff: bool = True
    """Whether to use exponential backoff for retries."""

    initial_retry_delay_seconds: float = 0.5
    """The initial retry delay in seconds."""
