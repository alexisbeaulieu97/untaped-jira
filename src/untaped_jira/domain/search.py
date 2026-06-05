"""JQL value objects for Jira issue search."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict


class JiraIssueSearchFilters(BaseModel):
    """Common issue search shortcuts plus an optional raw JQL base."""

    model_config = ConfigDict(frozen=True)

    raw_jql: str | None = None
    project: str | None = None
    assignee: str | None = None
    status: str | None = None
    text: str | None = None
    sprint: str | None = None

    def to_jql(self) -> str:
        base, order_by = _split_order_by(self.raw_jql.strip() if self.raw_jql else None)
        parts: list[str] = []
        if base:
            parts.append(f"({base})")
        parts.extend(self._shortcut_clauses())
        if not parts:
            parts = ["assignee = currentUser()", "resolution = Unresolved"]
        jql = " AND ".join(parts)
        return f"{jql} {order_by or 'ORDER BY updated DESC'}"

    def _shortcut_clauses(self) -> list[str]:
        clauses: list[str] = []
        if self.project:
            clauses.append(f"project = {_quote_project(self.project)}")
        if self.assignee:
            clauses.append(f"assignee = {_quote_or_current_user(self.assignee)}")
        if self.status:
            clauses.append(f"status = {_quote(self.status)}")
        if self.text:
            clauses.append(f"text ~ {_quote(self.text)}")
        if self.sprint:
            clauses.append(f"sprint = {_quote_sprint(self.sprint)}")
        return clauses


def _split_order_by(jql: str | None) -> tuple[str | None, str | None]:
    if not jql:
        return None, None
    match = re.search(r"\s+order\s+by\s+", jql, flags=re.IGNORECASE)
    if match is None:
        return jql, None
    return jql[: match.start()].strip(), jql[match.start() :].strip()


def _quote_project(value: str) -> str:
    return value if re.fullmatch(r"[A-Z][A-Z0-9_]*", value) else _quote(value)


def _quote_or_current_user(value: str) -> str:
    return "currentUser()" if value in {"@me", "me", "currentUser()"} else _quote(value)


def _quote_sprint(value: str) -> str:
    return value if value.isdecimal() else _quote(value)


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
