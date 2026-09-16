# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ZeptomailClient."""

from typing import Any, Dict, List, Optional, get_type_hints
from unittest.mock import AsyncMock, patch

import azure.connectors.zeptomail as zeptomail_module
import pytest
from azure.connectors.zeptomail import (
    ReplyToAddress,
    SendMailInput,
    SendTemplateMailInput,
    ZeptomailClient,
)
from azure.connectors.sdk.serialization import to_wire
from tests.generated_connector_test_utils import GeneratedConnectorContractTests
from tests.conftest import MockResponse


OPERATION_CONTRACTS = {
    "get_mail_agent": ("GET", False),
    "get_processed_emails": ("GET", False),
    "send_mail": ("POST", True),
    "send_template_mail": ("POST", True),
    "processed_mail_stats": ("GET", False),
}


class TestZeptomailClient(GeneratedConnectorContractTests):
    """Test the generated Zoho ZeptoMail client contract."""

    client_type = ZeptomailClient
    connector_module = zeptomail_module
    connector_name = "zeptomail"
    operation_contracts = OPERATION_CONTRACTS


@pytest.mark.asyncio
async def test_send_template_mail_preserves_mixed_values(
    mock_token_provider: Any,
) -> None:
    """Test the template-mail request serializes mixed merge values unchanged."""
    type_hints = get_type_hints(SendTemplateMailInput)
    model = SendTemplateMailInput(
        merge_key_detail=[{"key": "customer", "value": "Ada", "rank": 2}]
    )
    client = ZeptomailClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text='{"ok": true}'),
    ) as mock_send:
        result = await client.send_template_mail_async(model)

    assert type_hints["merge_key_detail"] == Optional[List[Dict[str, Any]]]
    mock_send.assert_awaited_once_with(
        "POST",
        "https://example.azure.com/connections/test/v1.0/email/template",
        body=model,
    )
    request_body = mock_send.call_args.kwargs["body"]
    assert to_wire(request_body)["merge_key_detail"] == [
        {"key": "customer", "value": "Ada", "rank": 2}
    ]
    assert result == {"ok": True}


def test_reply_to_uses_corrected_model_in_both_requests() -> None:
    """Test the corrected public type preserves both reply-to annotations."""
    expected_type = Optional[List[ReplyToAddress]]

    assert get_type_hints(SendMailInput)["reply_to"] == expected_type
    assert get_type_hints(SendTemplateMailInput)["reply_to"] == expected_type
    assert ReplyToAddress(address="reply@example.com", name="Reply").address == (
        "reply@example.com"
    )


@pytest.mark.asyncio
async def test_get_processed_emails_uses_exact_encoded_query(
    mock_token_provider: Any,
) -> None:
    """Test the processed-email route and every encoded query key and value."""
    client = ZeptomailClient(
        "https://example.azure.com/connections/test",
        token_provider=mock_token_provider,
    )
    expected_url = (
        "https://example.azure.com/connections/test/v1.0/email"
        "?mailagent_key=agent%2Bkey&subject=Quarterly%20report"
        "&from=sender%2Balias%40example.com&to=recipient%40example.com"
        "&date_from=2026-09-01%2F00%3A00&date_to=2026-09-02%2F00%3A00"
        "&request_id=request%2F42&is_hb=true&is_sb=false"
    )

    with patch.object(
        client._http_client,
        "send_async",
        new_callable=AsyncMock,
        return_value=MockResponse(status=200, text='{"data": []}'),
    ) as mock_send:
        result = await client.get_processed_emails_async(
            mailagent_key="agent+key",
            subject="Quarterly report",
            from_="sender+alias@example.com",
            to="recipient@example.com",
            date_from="2026-09-01/00:00",
            date_to="2026-09-02/00:00",
            request_id="request/42",
            is_hb=True,
            is_sb=False,
        )

    mock_send.assert_awaited_once_with("GET", expected_url, body=None)
    assert result == {"data": []}
