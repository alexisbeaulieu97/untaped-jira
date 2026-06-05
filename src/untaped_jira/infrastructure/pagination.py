"""Pagination helpers for Jira Data Center REST envelopes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

from untaped import HttpClient


def paginate_start_at(
    http: HttpClient,
    method: Literal["GET", "POST"],
    path: str,
    *,
    item_key: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    page_size: int,
    limit: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Walk Jira ``startAt`` / ``maxResults`` collection envelopes."""

    if limit is not None and limit <= 0:
        return
    emitted = 0
    start_at = 0
    while True:
        request_size = page_size
        if limit is not None:
            request_size = min(request_size, limit - emitted)
            if request_size <= 0:
                return
        request_params = {**(params or {}), "startAt": start_at, "maxResults": request_size}
        request_body = {**(body or {}), "startAt": start_at, "maxResults": request_size}
        payload = (
            http.get_json_dict(path, params=request_params)
            if method == "GET"
            else http.request_json("POST", path, json=request_body)
        )
        if not isinstance(payload, dict):
            return
        rows = payload.get(item_key)
        if not isinstance(rows, list) or not rows:
            return
        for row in rows:
            if isinstance(row, dict):
                yield row
                emitted += 1
                if limit is not None and emitted >= limit:
                    return
        if payload.get("isLast") is True:
            return
        total = payload.get("total")
        if isinstance(total, int) and start_at + len(rows) >= total:
            return
        start_at += len(rows)
