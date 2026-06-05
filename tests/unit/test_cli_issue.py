"""End-to-end CLI tests for `untaped jira issue`."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from untaped_jira import app


def test_me_reads_authenticated_jira_user(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        mock.get("/rest/api/2/myself").mock(
            return_value=httpx.Response(200, json={"name": "alexis", "displayName": "Alexis"})
        )
        result = CliRunner().invoke(app, ["me", "--format", "raw", "--columns", "name"])

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "alexis"


def test_issue_get_renders_key_first(jira_config: Path) -> None:
    payload = {
        "key": "ABC-1",
        "self": "https://jira.example.com/rest/api/2/issue/10001",
        "fields": {
            "summary": "Fix deploy",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Alexis"},
            "updated": "2026-06-05T10:00:00.000-0400",
        },
    }
    with respx.mock(base_url="https://jira.example.com") as mock:
        mock.get("/rest/api/2/issue/ABC-1").mock(return_value=httpx.Response(200, json=payload))
        result = CliRunner().invoke(
            app, ["issue", "get", "ABC-1", "--format", "raw", "--columns", "key"]
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "ABC-1"


def test_issue_search_sends_jql_and_renders_issue_keys(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.post("/rest/api/2/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 50,
                    "total": 1,
                    "issues": [{"key": "ABC-1", "fields": {"summary": "Fix deploy"}}],
                },
            )
        )
        result = CliRunner().invoke(
            app,
            [
                "issue",
                "search",
                "--project",
                "ABC",
                "--status",
                "Open",
                "--format",
                "raw",
                "--columns",
                "key",
            ],
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "ABC-1"
    request_json = json.loads(route.calls[0].request.content)
    assert request_json["jql"] == ('project = ABC AND status = "Open" ORDER BY updated DESC')


def test_issue_create_merges_template_and_flags(jira_config: Path, tmp_path: Path) -> None:
    template = tmp_path / "bug.yml"
    template.write_text("fields:\n  customfield_10000: old\n")
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.post("/rest/api/2/issue").mock(
            return_value=httpx.Response(
                201,
                json={"id": "10001", "key": "ABC-1", "self": "https://jira.example.com/ABC-1"},
            )
        )
        result = CliRunner().invoke(
            app,
            [
                "issue",
                "create",
                "--template",
                str(template),
                "--project",
                "ABC",
                "--issue-type",
                "Bug",
                "--summary",
                "Fix deploy",
                "--field",
                "customfield_10000=new",
                "--json-field",
                'customfield_10001={"value":"prod"}',
                "--format",
                "raw",
                "--columns",
                "key",
            ],
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "ABC-1"
    request_json = json.loads(route.calls[0].request.content)
    assert request_json["fields"] == {
        "customfield_10000": "new",
        "customfield_10001": {"value": "prod"},
        "project": {"key": "ABC"},
        "issuetype": {"name": "Bug"},
        "summary": "Fix deploy",
    }


def test_issue_edit_sends_body_file_and_overlays_flags(jira_config: Path, tmp_path: Path) -> None:
    body_file = tmp_path / "edit.yml"
    body_file.write_text("fields:\n  summary: old\n")
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.put("/rest/api/2/issue/ABC-1").mock(return_value=httpx.Response(204))
        result = CliRunner().invoke(
            app,
            [
                "issue",
                "edit",
                "ABC-1",
                "--body-file",
                str(body_file),
                "--summary",
                "new",
                "--field",
                "customfield_10000=value",
                "--format",
                "raw",
                "--columns",
                "key",
            ],
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "ABC-1"
    request_json = json.loads(route.calls[0].request.content)
    assert request_json["fields"] == {
        "summary": "new",
        "customfield_10000": "value",
    }


def test_issue_comment_reads_body_from_stdin(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.post("/rest/api/2/issue/ABC-1/comment").mock(
            return_value=httpx.Response(201, json={"id": "700"})
        )
        result = CliRunner().invoke(
            app,
            ["issue", "comment", "ABC-1", "--format", "raw", "--columns", "id"],
            input="hello from stdin\n",
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "700"
    assert json.loads(route.calls[0].request.content) == {"body": "hello from stdin"}


def test_issue_transition_by_name_rejects_ambiguous_match(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        mock.get("/rest/api/2/issue/ABC-1/transitions").mock(
            return_value=httpx.Response(
                200,
                json={"transitions": [{"id": "1", "name": "Done"}, {"id": "2", "name": "done"}]},
            )
        )
        result = CliRunner().invoke(app, ["issue", "transition", "ABC-1", "--to", "done"])

    assert result.exit_code != 0
    assert "multiple transitions" in result.output or "multiple transitions" in str(
        result.exception
    )


def test_issue_transition_by_id_posts_transition(jira_config: Path) -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.post("/rest/api/2/issue/ABC-1/transitions").mock(
            return_value=httpx.Response(204)
        )
        result = CliRunner().invoke(
            app,
            [
                "issue",
                "transition",
                "ABC-1",
                "--id",
                "31",
                "--format",
                "raw",
                "--columns",
                "transition_id",
            ],
        )

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "31"
    assert json.loads(route.calls[0].request.content) == {"transition": {"id": "31"}}
