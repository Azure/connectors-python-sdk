# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ZeptomailClient."""

from typing import Any, Dict, List, Optional, get_type_hints

import azure.connectors.zeptomail as zeptomail_module
from azure.connectors.zeptomail import SendTemplateMailInput, ZeptomailClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


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


def test_merge_key_detail_preserves_mixed_values() -> None:
    """Test fixed strings and additional numeric values remain representable."""
    type_hints = get_type_hints(SendTemplateMailInput)
    model = SendTemplateMailInput(
        merge_key_detail=[{"key": "customer", "value": "Ada", "rank": 2}]
    )

    assert type_hints["merge_key_detail"] == Optional[List[Dict[str, Any]]]
    assert model.merge_key_detail is not None
    assert model.merge_key_detail[0] == {
        "key": "customer",
        "value": "Ada",
        "rank": 2,
    }
