# ------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# ------------------------------------------------------------

"""Verify Azure Core JSON decoding through the generated async client."""

from __future__ import annotations

import json

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from azure.core.credentials import AzureKeyCredential

from azure.connectors.jira import JiraClient


@pytest.mark.parametrize("timeout", [None, 5.0, 0.0])
@pytest.mark.parametrize(
    ("content_type", "payload"),
    [
        ("application/json", b'\xef\xbb\xbf{"issues":[{"id":"bom"}],"isLast":true}'),
        (
            "application/json; charset=utf-8",
            b'\xef\xbb\xbf{"issues":[{"id":"bom"}],"isLast":true}',
        ),
        ("application/json", b'{"issues":[{"id":"plain"}],"isLast":true}'),
        (
            "application/json; charset=windows-1252",
            b'{"issues":[{"id":"caf\xe9"}],"isLast":true}',
        ),
    ],
)
@pytest.mark.asyncio
async def test_generated_pager_decodes_json_and_preserves_raw_bytes(
    timeout: float | None,
    content_type: str,
    payload: bytes,
) -> None:
    """Decode BOM JSON and charset controls without changing response bytes."""
    async def serve_response(request: web.Request) -> web.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return web.Response(body=payload, headers={"Content-Type": content_type})

    application = web.Application()
    application.router.add_get("/{path:.*}", serve_response)
    server = TestServer(application)
    await server.start_server()
    snapshots = []
    request_options = {} if timeout is None else {"timeout": timeout}
    try:
        async with JiraClient(
            str(server.make_url("/connections/test")),
            credential=AzureKeyCredential("test-key"),
        ) as client:
            issues = [
                issue async for issue in client.list_issues(
                    response_hook=lambda response, headers: snapshots.append(response),
                    **request_options,
                )
            ]
    finally:
        await server.close()

    expected_text = payload.decode(
        "windows-1252" if "windows-1252" in content_type else "utf-8-sig",
    )
    assert issues == json.loads(expected_text)["issues"]
    assert len(snapshots) == 1
    assert snapshots[0].content == payload
    assert json.loads(snapshots[0].text) == json.loads(expected_text)
