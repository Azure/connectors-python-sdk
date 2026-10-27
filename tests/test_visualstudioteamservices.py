# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Tests for the Azure DevOps (VSTS) connector."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from azure.core.credentials import AzureKeyCredential

from azure.connectors import visualstudioteamservices
from azure.connectors.sdk import ConnectorException
from azure.connectors.sdk.serialization import to_wire
from azure.connectors.visualstudioteamservices import (
    CreateWorkItemCommentRequest,
    QueueBuildRequest,
    VisualstudioteamservicesClient,
)
from tests.conftest import MockResponse
from tests.generated_connector_test_utils import GeneratedConnectorContractTests


BASE_URL = "https://example.azure.com/connections/vsts"


class TestVisualstudioteamservicesClient(GeneratedConnectorContractTests):
    """Check every callable operation and all generated model wire names."""

    client_type = VisualstudioteamservicesClient
    connector_module = visualstudioteamservices
    connector_name = "visualstudioteamservices"
    operation_contracts = {
        "search_work_items": ("POST", True),
        "get_build": ("GET", False),
        "list_build_timeline": ("GET", False),
        "list_accounts": ("GET", False),
        "get_profile": ("GET", False),
        "list_iterations": ("GET", False),
        "list_build_branches": ("GET", False),
        "list_builds": ("GET", False),
        "queue_new_build": ("POST", True),
        "list_build_requesters": ("GET", False),
        "list_git_repositories": ("GET", False),
        "list_projects": ("GET", False),
        "list_release_definitions": ("GET", False),
        "create_release": ("POST", True),
        "http_request": ("POST", True),
        "list_work_item_fields": ("GET", False),
        "list_work_item_types": ("GET", False),
        "get_work_item_details": ("GET", False),
        "update_work_item": ("PATCH", True),
        "get_work_item_details_v2": ("GET", False),
        "list_work_item_children": ("GET", False),
        "get_work_item_attachment": ("GET", False),
        "get_work_item_comments": ("GET", False),
        "create_work_item_comment": ("POST", True),
        "add_work_item_link": ("POST", True),
        "delete_work_item_link": ("POST", True),
        "update_work_item_comment": ("PATCH", True),
        "delete_work_item_comment": ("DELETE", False),
        "create_work_item": ("PATCH", True),
        "list_root_query_folders": ("GET", False),
        "list_queries_in_folder": ("GET", False),
        "list_work_items": ("GET", False),
        "list_pipelines": ("GET", False),
        "list_pipeline_runs": ("GET", False),
        "run_pipeline": ("POST", True),
        "get_pipeline_run": ("GET", False),
        "get_git_item": ("GET", False),
        "list_git_refs_with_filter": ("GET", False),
        "create_git_push": ("POST", True),
        "create_git_pull_request": ("POST", True),
        "update_git_pull_request": ("PATCH", True),
        "list_query_results": ("GET", False),
        "list_teams": ("GET", False),
        "list_build_definitions": ("GET", False),
        "list_git_refs": ("GET", False),
        "list_team_members": ("GET", False),
        "get_work_item_schema_for_update": ("GET", False),
        "get_work_item_schema": ("GET", False),
        "get_response_work_item_schema": ("GET", False),
        "get_query_result_work_item_schema": ("GET", False),
        "get_work_item_schema_for_create": ("GET", False),
    }


@pytest.mark.asyncio
async def test_queue_build_preserves_wire_body_and_encodes_project() -> None:
    """Serialize the pinned QueueBuildRequest schema without losing wire names."""
    async with VisualstudioteamservicesClient(BASE_URL, AzureKeyCredential("test-key")) as client:
        with patch.object(
            client.http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(200, '{"id": 42, "status": "notStarted"}'),
        ) as send:
            build = await client.queue_new_build(
                input=QueueBuildRequest(
                    source_branch="refs/heads/main", parameters='{"runTests":true}',
                ),
                project="Project/Name",
                account="example organization",
                build_def_id="7",
            )

    assert build == {"id": 42, "status": "notStarted"}
    assert send.call_args.args[0] == "POST"
    assert urlsplit(send.call_args.args[1]).path.endswith("/Project%2FName/_apis/build/builds")
    assert parse_qs(urlsplit(send.call_args.args[1]).query) == {
        "account": ["example organization"], "buildDefId": ["7"],
    }
    assert to_wire(send.call_args.kwargs["body"]) == {
        "sourceBranch": "refs/heads/main", "parameters": '{"runTests":true}',
    }


@pytest.mark.asyncio
async def test_update_comment_preserves_patch_body_and_query() -> None:
    """Forward the required comment text and optional format on PATCH."""
    async with VisualstudioteamservicesClient(BASE_URL, AzureKeyCredential("test-key")) as client:
        with patch.object(
            client.http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(200, '{"id": 3, "text": "Updated"}'),
        ) as send:
            comment = await client.update_work_item_comment(
                input=CreateWorkItemCommentRequest(text="Updated"),
                work_item_id=42,
                comment_id=3,
                account="organization",
                project="Project Name",
                format="Markdown",
            )

    assert comment == {"id": 3, "text": "Updated"}
    assert send.call_args.args[0] == "PATCH"
    assert urlsplit(send.call_args.args[1]).path.endswith("/_apis/wit/workitems/42/comments/3")
    assert parse_qs(urlsplit(send.call_args.args[1]).query) == {
        "account": ["organization"], "project": ["Project Name"], "format": ["Markdown"],
    }
    assert to_wire(send.call_args.kwargs["body"]) == {"text": "Updated"}


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 404, 500])
async def test_delete_comment_raises_for_each_error_status(status: int) -> None:
    """Keep client, missing-target, and server failures distinct on void DELETE."""
    async with VisualstudioteamservicesClient(BASE_URL, AzureKeyCredential("test-key")) as client:
        with patch.object(
            client.http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(status, '{"message": "Delete failed"}'),
        ):
            with pytest.raises(ConnectorException) as error:
                await client.delete_work_item_comment(
                    work_item_id=42, comment_id=3, account="organization", project="Project",
                )

    assert error.value.status_code == status


@pytest.mark.asyncio
async def test_delete_comment_accepts_empty_success() -> None:
    """Check the successful void DELETE route without inventing a response body."""
    async with VisualstudioteamservicesClient(BASE_URL, AzureKeyCredential("test-key")) as client:
        with patch.object(
            client.http_client,
            "send",
            new_callable=AsyncMock,
            return_value=MockResponse(204),
        ) as send:
            deleted = await client.delete_work_item_comment(
                work_item_id=42, comment_id=3, account="organization", project="Project",
            )

    assert deleted is None
    assert send.call_args.args[0] == "DELETE"
    assert send.call_args.kwargs["body"] is None
