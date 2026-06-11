"""untaped-jira: manage Jira Data Center tickets from untaped.

``app`` and ``JiraClient`` are resolved lazily (PEP 562): the plugin manifest
points core at ``untaped_jira.cli:app``, so importing this package must not
pull in the CLI module (or the HTTP stack) until they are actually used.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from untaped_jira.settings import JiraSettings

if TYPE_CHECKING:
    from cyclopts import App

    from untaped_jira.infrastructure import JiraClient as JiraClient

    app: App

__all__ = ["JiraClient", "JiraSettings", "app"]


def __getattr__(name: str) -> object:
    """Resolve the lazy ``app`` and ``JiraClient`` exports on first access."""
    # Deferred imports are the point of this hook: they keep package import
    # cheap so core's lazy CLI mounting never loads the command tree early.
    if name == "app":
        from untaped_jira.cli import app  # noqa: PLC0415

        return app
    if name == "JiraClient":
        from untaped_jira.infrastructure import JiraClient  # noqa: PLC0415

        return JiraClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
