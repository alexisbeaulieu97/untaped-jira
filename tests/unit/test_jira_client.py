"""Unit tests for the Jira REST client."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from pydantic import SecretStr
from untaped import ConfigError, HttpSettings

from untaped_jira import JiraClient, JiraSettings


def _settings() -> JiraSettings:
    return JiraSettings(
        base_url="https://jira.example.com",
        token=SecretStr("jira_pat"),
    )


def test_client_sends_pat_bearer_header_and_joins_api_prefix() -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.get("/rest/api/2/myself").mock(
            return_value=httpx.Response(200, json={"name": "alexis", "displayName": "Alexis"})
        )
        with JiraClient(_settings()) as client:
            assert client.me()["name"] == "alexis"

    assert route.calls[0].request.headers["authorization"] == "Bearer jira_pat"
    assert route.calls[0].request.headers["accept"] == "application/json"


def test_client_uses_core_tls_verify_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[HttpSettings] = []

    def fake_resolve_verify(http: HttpSettings) -> bool:
        seen.append(http)
        return False

    monkeypatch.setattr(
        "untaped_jira.infrastructure.jira_client.resolve_verify",
        fake_resolve_verify,
    )

    client = JiraClient(_settings(), http=HttpSettings(verify_ssl=False))
    client.close()

    assert seen == [HttpSettings(verify_ssl=False)]


def test_client_requires_base_url() -> None:
    config = JiraSettings(token=SecretStr("jira_pat"))

    with pytest.raises(ConfigError, match=r"jira\.base_url"):
        JiraClient(config)


def test_client_requires_non_blank_token() -> None:
    config = JiraSettings(base_url="https://jira.example.com", token=SecretStr("   "))

    with pytest.raises(ConfigError, match=r"jira\.token"):
        JiraClient(config)


def test_search_issues_posts_jql_and_paginates() -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.post("/rest/api/2/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 2,
                    "total": 1,
                    "issues": [{"key": "ABC-1", "fields": {"summary": "one"}}],
                },
            )
        )
        with JiraClient(_settings()) as client:
            rows = list(client.search_issues("project = ABC", limit=1))

    assert rows[0]["key"] == "ABC-1"
    request_json = json.loads(route.calls[0].request.content)
    assert request_json["jql"] == "project = ABC"
    assert request_json["maxResults"] == 1


def test_agile_list_boards_uses_agile_prefix() -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.get("/rest/agile/1.0/board").mock(
            return_value=httpx.Response(
                200,
                json={"startAt": 0, "maxResults": 50, "isLast": True, "values": [{"id": 7}]},
            )
        )
        with JiraClient(_settings()) as client:
            rows = list(client.list_boards(project_key_or_id="ABC", limit=10))

    assert rows == [{"id": 7}]
    assert route.calls[0].request.url.params["projectKeyOrId"] == "ABC"
