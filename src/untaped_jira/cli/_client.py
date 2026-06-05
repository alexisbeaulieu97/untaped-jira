"""Shared CLI composition root for opening a Jira client."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from untaped import get_config_section, get_core_settings, profile_override

from untaped_jira.settings import JiraSettings

if TYPE_CHECKING:
    from collections.abc import Iterator

    from untaped_jira.infrastructure import JiraClient


@contextmanager
def open_client(profile: str | None = None) -> Iterator[JiraClient]:
    """Build a context-managed Jira client from active untaped settings."""

    from untaped_jira.infrastructure import JiraClient  # noqa: PLC0415

    with profile_override(profile):
        settings = get_core_settings()
        with JiraClient(get_config_section("jira", JiraSettings), http=settings.http) as client:
            yield client


def current_jira_settings(profile: str | None = None) -> JiraSettings:
    """Read active Jira settings without opening an HTTP client."""

    with profile_override(profile):
        return get_config_section("jira", JiraSettings)
