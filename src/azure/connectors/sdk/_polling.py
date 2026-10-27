# Copyright (c) Microsoft Corporation. All rights reserved.

"""Shared helpers for connector long-running operation polling."""

import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Mapping, Optional
from urllib.parse import SplitResult, urljoin, urlsplit

from .response import ConnectorResponseSnapshot

DEFAULT_POLLING_INTERVAL_SECONDS = 1.0


def get_header(headers: Mapping[str, str], name: str) -> Optional[str]:
    """Return a response header using HTTP case-insensitive matching."""
    normalized_name = name.casefold()
    return next(
        (
            value
            for header_name, value in headers.items()
            if header_name.casefold() == normalized_name
        ),
        None,
    )


def get_location(response: ConnectorResponseSnapshot) -> Optional[str]:
    """Return the Location polling URL from a connector response."""
    return get_header(response.headers, "Location")


def _split_safe_url(value: str) -> SplitResult:
    """Reject URL spellings that HTTP transports can interpret differently."""
    if "\\" in value or any(
        ord(character) <= 32 or ord(character) == 127 for character in value
    ):
        raise ValueError(
            "Polling URLs must not contain backslashes or control characters."
        )
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith("//"):
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or "@" in parsed.netloc
            or "%" in parsed.netloc
        ):
            raise ValueError(
                "Polling URLs must use an unambiguous HTTP authority without userinfo."
            )
        authority = parsed.hostname
        if ":" in authority:
            authority = f"[{authority}]"
        if parsed.port is not None:
            authority += f":{parsed.port}"
        if parsed.netloc.casefold() != authority.casefold():
            raise ValueError("Polling URLs must use an unambiguous HTTP authority.")
    return parsed


def resolve_polling_url(
    polling_url: str,
    connection_runtime_url: str,
    current_polling_url: Optional[str] = None,
) -> str:
    """Route a connector polling URL through the authenticated runtime origin."""
    parsed_connection = _split_safe_url(connection_runtime_url)
    parsed_polling_url = _split_safe_url(polling_url)
    if parsed_connection.hostname is None:
        raise ValueError("Polling URLs must include a hostname.")
    if polling_url.startswith("/"):
        return f"{connection_runtime_url}{polling_url}"

    if not parsed_polling_url.scheme and not parsed_polling_url.netloc:
        base_url = current_polling_url or f"{connection_runtime_url.rstrip('/')}/"
        if _split_safe_url(base_url).hostname is None:
            raise ValueError("Polling URLs must include a hostname.")
        return resolve_polling_url(
            urljoin(base_url, polling_url), connection_runtime_url
        )

    polling_hostname = parsed_polling_url.hostname
    connection_hostname = parsed_connection.hostname
    if polling_hostname is None or connection_hostname is None:
        raise ValueError("Polling URLs must include a hostname.")

    polling_port = parsed_polling_url.port or (
        443 if parsed_polling_url.scheme == "https" else 80
    )
    connection_port = parsed_connection.port or (
        443 if parsed_connection.scheme == "https" else 80
    )
    if polling_hostname.casefold() == connection_hostname.casefold():
        if (
            parsed_polling_url.scheme == parsed_connection.scheme
            and polling_port == connection_port
        ):
            return parsed_connection._replace(
                path=parsed_polling_url.path,
                query=parsed_polling_url.query,
                fragment=parsed_polling_url.fragment,
            ).geturl()
        raise ValueError(
            "Polling URL origin must use the connection runtime scheme and port."
        )

    suffix = parsed_polling_url.path
    if parsed_polling_url.query:
        suffix += f"?{parsed_polling_url.query}"
    return f"{connection_runtime_url}{suffix}"


def get_retry_after_seconds(response: ConnectorResponseSnapshot) -> float:
    """Return the server-requested delay or the default polling interval."""
    retry_after = get_header(response.headers, "Retry-After")
    if retry_after is None:
        return DEFAULT_POLLING_INTERVAL_SECONDS

    try:
        delay = float(retry_after)
        return (
            max(0.0, delay)
            if math.isfinite(delay)
            else DEFAULT_POLLING_INTERVAL_SECONDS
        )
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(retry_after)
        except (TypeError, ValueError):
            return DEFAULT_POLLING_INTERVAL_SECONDS

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(
            0.0,
            (retry_at - datetime.now(timezone.utc)).total_seconds(),
        )


def get_polling_status(response: Optional[ConnectorResponseSnapshot]) -> str:
    """Map an HTTP response to an Azure Core polling status string."""
    if response is None:
        return "NotStarted"
    if response.status == 202:
        return "InProgress"
    if 200 <= response.status < 300:
        return "Succeeded"
    return "Failed"
