# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for OrderfulClient."""

from typing import get_type_hints

import azure.connectors.orderful as orderful_module
from azure.connectors.orderful import OrderfulClient, TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    "create_transaction": ("POST", True),
    "get_transaction_by_id": ("GET", False),
    "list_transactions": ("GET", False),
}


class TestOrderfulClient(GeneratedConnectorContractTests):
    """Test the generated Orderful client contract."""

    client_type = OrderfulClient
    connector_module = orderful_module
    connector_name = "orderful"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test the Orderful trigger remains a metadata-only operation."""
    assert set(TRIGGER_OPERATIONS) == {"Communication-Channel"}


def test_transaction_id_uses_integer_annotation() -> None:
    """Test transaction identifiers preserve the Swagger integer type."""
    type_hints = get_type_hints(OrderfulClient.get_transaction_by_id_async)

    assert type_hints["transaction_id"] is int
