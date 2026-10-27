# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Execute the Dataflows and Azure DevOps samples against mocked collections."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "connector,client_name,operation,label",
    [
        (
            "dataflows", "DataflowsClient", "list_groups_for_refresh_dataflow",
            "Workspaces or environments",
        ),
        ("visualstudioteamservices", "VisualstudioteamservicesClient", "list_projects", "Projects"),
    ],
    ids=["dataflows", "azure-devops"],
)
@pytest.mark.parametrize(
    "items", [[], [{"id": "item-1", "name": "Example"}]], ids=["empty", "populated"],
)
async def test_sample_prints_collected_items(
    connector: str,
    client_name: str,
    operation: str,
    label: str,
    items: list[dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Require both samples to consume their pager and close owned resources."""
    sample_path = (
        Path(__file__).parent.parent / "samples" / "sample_connector_usage"
        / f"sample_connector_usage_{connector}.py"
    )
    specification = importlib.util.spec_from_file_location(f"sample_{connector}", sample_path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    async def collection():
        for item in items:
            yield item

    credential_context = MagicMock()
    client_context = MagicMock()
    client = MagicMock()
    client_context.__aenter__.return_value = client
    getattr(client, operation).return_value = collection()
    monkeypatch.setattr(
        module, "DefaultAzureCredential", MagicMock(return_value=credential_context),
    )
    monkeypatch.setattr(module, client_name, MagicMock(return_value=client_context))
    monkeypatch.setattr(
        module, "CONNECTION_RUNTIME_URL", "https://example.azure.com/connections/test",
    )
    if connector == "visualstudioteamservices":
        monkeypatch.setattr(module, "ORGANIZATION", "organization")

    await module.main()

    assert capsys.readouterr().out == f"{label}: {items}\n"
    getattr(client, operation).assert_called_once_with(
        **(
            {"account": "organization"}
            if connector == "visualstudioteamservices"
            else {"workspace_type": "Workspace"}
        )
    )
    client_context.__aexit__.assert_awaited_once()
    credential_context.__aexit__.assert_awaited_once()
