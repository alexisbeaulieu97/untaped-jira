"""CLI tests for Jira project, board, and sprint lookup helpers."""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from untaped.testing import CliInvoker

from untaped_jira import app


def test_project_list_outputs_project_keys(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        mock.get("/rest/api/2/project").mock(
            return_value=httpx.Response(200, json=[{"id": "10000", "key": "ABC", "name": "App"}])
        )
        result = CliInvoker().invoke(
            app, ["project", "list", "--format", "raw", "--columns", "key"]
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "ABC"


def test_project_get_outputs_one_project(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        mock.get("/rest/api/2/project/ABC").mock(
            return_value=httpx.Response(200, json={"id": "10000", "key": "ABC", "name": "App"})
        )
        result = CliInvoker().invoke(
            app, ["project", "get", "ABC", "--format", "raw", "--columns", "key"]
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "ABC"


def test_project_get_missing_key_is_usage_error() -> None:
    result = CliInvoker().invoke(app, ["project", "get"])

    assert result.exit_code == 2, result.output
    assert result.stdout == ""
    assert "requires an argument" in result.stderr


def test_board_list_filters_by_project(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.get("/rest/agile/1.0/board").mock(
            return_value=httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 50,
                    "isLast": True,
                    "values": [{"id": 7, "name": "ABC Board", "type": "scrum"}],
                },
            )
        )
        result = CliInvoker().invoke(
            app, ["board", "list", "--project", "ABC", "--format", "raw", "--columns", "id"]
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "7"
    assert route.calls[0].request.url.params["projectKeyOrId"] == "ABC"


def test_sprint_list_uses_configured_default_board(jira_config: Path) -> None:
    jira_config.write_text(
        "jira:\n  base_url: https://jira.example.com\n  token: jira_pat\n  default_board_id: 7\n"
    )
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.get("/rest/agile/1.0/board/7/sprint").mock(
            return_value=httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 50,
                    "isLast": True,
                    "values": [{"id": 20, "name": "Sprint 20", "state": "active"}],
                },
            )
        )
        result = CliInvoker().invoke(
            app, ["sprint", "list", "--state", "active", "--format", "raw", "--columns", "id"]
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "20"
    assert route.calls[0].request.url.params["state"] == "active"
