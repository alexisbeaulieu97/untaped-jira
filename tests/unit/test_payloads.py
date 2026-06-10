"""Tests for Jira issue payload and template handling."""

from __future__ import annotations

from pathlib import Path

import pytest
from untaped.api import ConfigError

from untaped_jira.domain import build_issue_payload, parse_json_field_assignments, read_payload_file


def test_build_issue_payload_applies_overlay_precedence(tmp_path: Path) -> None:
    template = tmp_path / "bug.yml"
    template.write_text(
        "fields:\n"
        "  project:\n"
        "    key: OLD\n"
        "  summary: old summary\n"
        "  customfield_10000: old\n"
        "update:\n"
        "  labels:\n"
        "    - add: old\n"
    )
    base = read_payload_file(template)

    payload = build_issue_payload(
        base=base,
        project="ABC",
        issue_type="Bug",
        summary="new summary",
        description="new body",
        fields={"customfield_10000": "string value"},
        json_fields={"customfield_10001": {"value": "json value"}},
    )

    assert payload == {
        "fields": {
            "project": {"key": "ABC"},
            "issuetype": {"name": "Bug"},
            "summary": "new summary",
            "description": "new body",
            "customfield_10000": "string value",
            "customfield_10001": {"value": "json value"},
        },
        "update": {"labels": [{"add": "old"}]},
    }


def test_parse_json_field_assignments_rejects_invalid_json() -> None:
    with pytest.raises(ConfigError, match="--json-field"):
        parse_json_field_assignments(["customfield_10000={broken"])


def test_read_payload_file_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "bad.yml"
    path.write_text("- not\n- an\n- object\n")

    with pytest.raises(ConfigError, match="must contain an object"):
        read_payload_file(path)
