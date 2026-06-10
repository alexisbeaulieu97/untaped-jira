"""Jira issue payload and local template helpers."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from untaped.api import ConfigError


def read_payload_file(path: Path) -> dict[str, Any]:
    """Read a Jira-shaped YAML or JSON payload file."""

    try:
        text = path.read_text()
    except OSError as exc:
        raise ConfigError(f"could not read {path}: {exc}") from exc
    try:
        raw = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ConfigError(f"could not parse {path}: {exc}") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain an object")
    return dict(raw)


def parse_json_field_assignments(values: list[str] | None) -> dict[str, Any]:
    """Parse repeated ``KEY=JSON`` values for custom Jira fields."""

    parsed: dict[str, Any] = {}
    for entry in values or ():
        key, sep, raw_value = entry.partition("=")
        key = key.strip()
        if not sep or not key:
            raise ConfigError(f"--json-field expects KEY=JSON (got {entry!r})")
        try:
            parsed[key] = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"--json-field {key} contains invalid JSON: {exc}") from exc
    return parsed


def build_issue_payload(
    *,
    base: dict[str, Any] | None = None,
    project: str | None = None,
    issue_type: str | None = None,
    summary: str | None = None,
    description: str | None = None,
    fields: dict[str, str] | None = None,
    json_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge a Jira-shaped base payload with CLI convenience overlays."""

    payload = deepcopy(base or {})
    raw_fields = payload.setdefault("fields", {})
    if not isinstance(raw_fields, dict):
        raise ConfigError("Jira payload `fields` must be an object")
    if "update" in payload and not isinstance(payload["update"], dict):
        raise ConfigError("Jira payload `update` must be an object")
    if project is not None:
        raw_fields["project"] = {"key": project}
    if issue_type is not None:
        raw_fields["issuetype"] = {"name": issue_type}
    if summary is not None:
        raw_fields["summary"] = summary
    if description is not None:
        raw_fields["description"] = description
    raw_fields.update(fields or {})
    raw_fields.update(json_fields or {})
    return payload
