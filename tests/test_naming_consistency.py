# Copyright (c) Microsoft Corporation. All rights reserved.

"""Checks that connector test classes spell their client prefix like the generated client."""

import ast
from pathlib import Path

from azure.connectors._client_registry import CLIENT_REGISTRY

_TESTS_DIRECTORY = Path(__file__).parent
_PREFIXES = sorted(
    (client_name[: -len("Client")] for client_name in CLIENT_REGISTRY),
    key=len,
    reverse=True,
)


def _find_misspelled_prefix(class_name: str) -> str | None:
    """Return the canonical prefix when a test class spells it with different casing."""
    body = class_name[len("Test"):]
    for prefix in _PREFIXES:
        spelled = body[: len(prefix)]
        next_character = body[len(prefix): len(prefix) + 1]
        if spelled.lower() != prefix.lower() or (next_character and not next_character.isupper()):
            continue
        return prefix if spelled != prefix else None
    return None


def test_connector_test_classes_use_canonical_prefix_casing() -> None:
    mismatches = []
    for path in sorted(_TESTS_DIRECTORY.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                prefix = _find_misspelled_prefix(node.name)
                if prefix is not None:
                    mismatches.append(
                        f"{path.name}:{node.lineno} {node.name} (expected prefix {prefix})"
                    )

    message = "Test classes must use the generated client prefix:\n"
    assert not mismatches, message + "\n".join(mismatches)


def test_find_misspelled_prefix_requires_word_boundary() -> None:
    assert _find_misspelled_prefix("TestGooglecalendarApiSurface") == "GoogleCalendar"
    assert _find_misspelled_prefix("TestGoogleCalendarApiSurface") is None
    assert _find_misspelled_prefix("TestMqttTopics") is None
    assert _find_misspelled_prefix("TestSharedHelpers") is None
