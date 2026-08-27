# Copyright (c) Microsoft Corporation. All rights reserved.

"""Contract tests for ImpexiumClient."""

import azure.connectors.impexium as impexium_module
from azure.connectors.impexium import ImpexiumClient, TRIGGER_OPERATIONS
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


OPERATION_CONTRACTS = {
    **dict.fromkeys(
        [
            "delete_a_category_for_an_individual",
            "delete_a_category_for_an_organization",
            "delete_record_from_custom_data_table",
        ],
        ("DELETE", False),
    ),
    **dict.fromkeys(
        [
            "delete_an_individual_web_link",
            "delete_an_organization_web_link",
        ],
        ("DELETE", True),
    ),
    **dict.fromkeys(
        [
            "awards_get_individual_award_recipients",
            "awards_get_organization_award_recipients",
            "find_customer_phone",
            "find_individual_id_or_email",
            "find_members_by_name",
            "find_members_or_individuals_by_first_and_last_name",
            "find_members_or_individuals_by_first_name",
            "find_members_or_individuals_by_last_name",
            "find_members_or_individuals_by_name",
            "get_a_list_of_all_services_of_an_organization",
            "get_a_list_of_licenses",
            "get_abandoned_checkouts",
            "get_all_committees",
            "get_all_event_registrations_information_for_an_individual",
            "get_all_events",
            "get_all_open_orders_for_an_individual",
            "get_all_states_by_country",
            "get_committee_information_for_an_individual",
            "get_committee_members_by_committee_id_or_code",
            "get_course_attendees",
            "get_individual_active_memberships",
            "get_individual_custom_field_values",
            "get_individual_inactive_memberships",
            "get_individuals_active_subscriptions",
            "get_individuals_relationships",
            "get_list_of_active_certifications_for_an_individual",
            "get_list_of_active_certifications_for_an_organization",
            "get_nominees_by_committee",
            "get_organization_active_memberships",
            "get_organization_custom_field_values",
            "get_organization_inactive_memberships",
            "get_organizations_active_subscriptions",
            "get_organizations_relationships",
            "get_positions_by_committee",
            "get_purchases_for_an_individual",
            "get_sub_committees",
            "get_upcoming_events",
            "individuals_lookup_by_name",
            "list_all_awards",
            "list_all_countries",
            "list_all_event_cancellations_by_event",
            "list_all_exhibitors",
            "list_all_exhibits",
            "list_all_individuals",
            "list_all_open_customer_request",
            "list_completed_user_tasks_by_user_id_or_email",
            "list_of_all_individual_members",
            "list_of_all_organization_members",
            "list_of_customer_relationships",
            "list_of_exams",
            "list_pending_user_tasks_by_user_id_or_email",
            "list_registrants",
            "organization_get_profile",
            "organization_lookup_by_name",
        ],
        ("GET", False),
    ),
    **dict.fromkeys(
        [
            "add_a_new_task",
            "add_a_service_to_an_organization",
            "add_activity",
            "add_activity_to_organization",
            "add_activity_to_sales_opportunity",
            "add_categories_for_an_individual",
            "add_categories_for_an_organization",
            "add_customer_request",
            "add_email_to_individual",
            "add_email_to_organization",
            "add_exam_scores",
            "add_individual",
            "add_nominee",
            "add_note_to_sales_opportunity",
            "add_notification_to_individual",
            "add_or_update_a_list_of_custom_fields_per_individual",
            "add_or_update_a_list_of_custom_fields_per_organization",
            "add_or_update_address_to_individual",
            "add_or_update_address_to_organization",
            "add_organization",
            "add_phone_to_individual",
            "add_phone_to_organization",
            "add_relationship_to_individual",
            "add_to_committee",
            "add_web_link_for_individual",
            "add_web_link_for_organization",
            "assign_task_to_a_user",
            "awards_add_award_nomination",
            "individual_add_education_credit",
            "individual_add_note",
            "organization_add_note",
            "register_an_individual_for_a_free_session",
            "save_relationship_for_organization",
            "update_custom_field_value",
        ],
        ("POST", True),
    ),
    **dict.fromkeys(
        [
            "awards_update_award_nomination",
            "mark_registrant_attended",
            "update_an_individual_email",
            "update_committee_member",
            "update_customer_request",
            "update_organization",
            "update_phone_for_an_individual",
            "update_phone_for_an_organization",
            "update_task_by_task_number",
            "update_user_task_progress_or_mark_as_completed",
        ],
        ("PUT", True),
    ),
}

EXPECTED_TRIGGER_OPERATIONS = {
    "When-Committee-Member-Updated",
    "When-Customer-Address-Updated",
    "When-Customer-Custom-Field-Value-Updated",
    "When-Customer-Is-Merged",
    "When-Customer-Phone-Updated",
    "When-Customer-Relationship-Updated",
    "When-Email-Updated",
    "When-Event-Registration-Substituted",
    "When-Individual-Created",
    "When-Individual-Deleted",
    "When-Individual-Request-Forgotten",
    "When-Membership-Terminated",
    "When-Purchase-Paid",
    "When-Request-Updated",
    "When-product-purchased",
    "When-purchase-cancelled",
}


class TestImpexiumClient(GeneratedConnectorContractTests):
    """Test the generated Impexium client contract."""

    client_type = ImpexiumClient
    connector_module = impexium_module
    connector_name = "impexium"
    operation_contracts = OPERATION_CONTRACTS


def test_trigger_operations() -> None:
    """Test Impexium trigger metadata remains complete."""
    assert set(TRIGGER_OPERATIONS) == EXPECTED_TRIGGER_OPERATIONS
