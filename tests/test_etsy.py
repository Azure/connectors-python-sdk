# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for EtsyClient."""

import azure.connectors.etsy as etsy_module
from azure.connectors.etsy import EtsyClient
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    **dict.fromkeys(
        [
            "listing_delete",
            "listing_delete_file",
            "listing_delete_image",
            "listing_delete_property",
            "shipping_delete_profile",
            "shipping_delete_profile_destination",
            "shipping_delete_profile_upgrade",
        ],
        ("DELETE", False),
    ),
    **dict.fromkeys(
        [
            "listing_get",
            "listing_get_active",
            "listing_get_active_by_shop",
            "listing_get_by_id",
            "listing_get_by_receipt",
            "listing_get_by_section_id",
            "listing_get_featured",
            "listing_get_file",
            "listing_get_files",
            "listing_get_image",
            "listing_get_images",
            "listing_get_inventory",
            "listing_get_offering",
            "listing_get_product",
            "listing_get_properties",
            "listing_get_properties_by_taxonomy",
            "listing_get_property",
            "listing_get_shop",
            "listing_get_taxonomy_nodes",
            "listing_get_translation",
            "listing_get_variation",
            "payment_get_entry_id",
            "payment_get_receipt",
            "payment_ledger_entries",
            "payments_get",
            "ping",
            "receipt_get",
            "receipts_get",
            "reviews_get",
            "shipping_carriers",
            "shipping_get_destinations",
            "shipping_get_profile",
            "shipping_get_profile_upgrades",
            "shipping_profiles",
            "shop_get_by_owner_id",
            "shop_get_section",
            "shop_get_sections",
            "shop_search",
            "transaction_get",
            "transaction_get_shop",
            "transaction_receipt",
            "transactions_listing",
            "user_get",
            "user_get_address",
            "user_get_addresses",
        ],
        ("GET", False),
    ),
    **dict.fromkeys(
        [
            "listing_create",
            "listing_create_translation",
            "listing_update_variation",
            "listing_upload",
            "listing_upload_image",
            "receipt_create_shipment",
            "shipping_create_destination",
            "shipping_create_profile",
            "shipping_create_upgrade",
            "shop_create_section",
        ],
        ("POST", True),
    ),
    **dict.fromkeys(
        [
            "listing_update",
            "listing_update_inventory",
            "listing_update_property",
            "listing_update_translation",
            "shipping_update_profile",
            "shipping_update_profile_destination",
            "shipping_update_profile_upgrade",
            "shop_update",
        ],
        ("PUT", True),
    ),
}


class TestEtsyClient(GeneratedConnectorContractTests):
    """Test the generated Etsy client contract."""

    client_type = EtsyClient
    connector_module = etsy_module
    connector_name = "etsy"
    operation_contracts = OPERATION_CONTRACTS
