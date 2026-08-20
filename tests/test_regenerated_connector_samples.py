# Copyright (c) Microsoft Corporation. All rights reserved.

"""Import tests for samples affected by connector regeneration."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SAMPLE_DIRECTORY = (
    Path(__file__).parent.parent / "samples" / "sample_connector_usage"
)


@pytest.mark.parametrize(
    "connector_name",
    [
        "docusign",
        "github",
        "googletasks",
        "pdfco",
        "planner",
        "salesforce",
        "signinghub",
        "slack",
        "smtp",
        "wordonlinebusiness",
        "yammer",
        "zohosign",
    ],
)
def test_regenerated_connector_sample_imports(connector_name: str) -> None:
    """Test regenerated connector samples import their current public models."""
    sample_path = SAMPLE_DIRECTORY / f"sample_connector_usage_{connector_name}.py"
    specification = importlib.util.spec_from_file_location(
        f"sample_connector_usage_{connector_name}",
        sample_path,
    )

    assert specification is not None
    assert specification.loader is not None

    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
