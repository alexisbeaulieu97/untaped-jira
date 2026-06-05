"""Tests for Jira Data Center pagination helpers."""

from __future__ import annotations

import httpx
import respx
from untaped import HttpClient

from untaped_jira.infrastructure.pagination import paginate_start_at


def test_paginate_start_at_reads_named_collection_until_total() -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        mock.post("/rest/api/2/search").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "startAt": 0,
                        "maxResults": 1,
                        "total": 2,
                        "issues": [{"key": "ABC-1"}],
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "startAt": 1,
                        "maxResults": 1,
                        "total": 2,
                        "issues": [{"key": "ABC-2"}],
                    },
                ),
            ]
        )
        with HttpClient(base_url="https://jira.example.com") as http:
            rows = list(
                paginate_start_at(
                    http,
                    "POST",
                    "/rest/api/2/search",
                    item_key="issues",
                    body={"jql": "project = ABC"},
                    page_size=1,
                    limit=2,
                )
            )

    assert [row["key"] for row in rows] == ["ABC-1", "ABC-2"]


def test_paginate_start_at_honors_limit_on_first_page() -> None:
    with respx.mock(base_url="https://jira.example.com") as mock:
        route = mock.get("/rest/agile/1.0/board").mock(
            return_value=httpx.Response(
                200,
                json={"startAt": 0, "maxResults": 1, "isLast": True, "values": [{"id": 1}]},
            )
        )
        with HttpClient(base_url="https://jira.example.com") as http:
            rows = list(
                paginate_start_at(
                    http,
                    "GET",
                    "/rest/agile/1.0/board",
                    item_key="values",
                    page_size=50,
                    limit=1,
                )
            )

    assert rows == [{"id": 1}]
    assert route.calls[0].request.url.params["maxResults"] == "1"
