"""Shared CLI composition root for opening a Jira client."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from untaped.api import plugin_context

from untaped_jira.settings import JiraSettings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from untaped_jira.infrastructure import JiraClient


@contextmanager
def open_client(profile: str | None = None) -> Iterator[JiraClient]:
    """Build a context-managed Jira client from active untaped settings."""

    from untaped_jira.infrastructure import JiraClient  # noqa: PLC0415

    ctx = plugin_context(profile)
    with JiraClient(ctx.section("jira", JiraSettings), http=ctx.http) as client:
        yield client


def current_jira_settings(profile: str | None = None) -> JiraSettings:
    """Read active Jira settings without opening an HTTP client."""

    return plugin_context(profile).section("jira", JiraSettings)
