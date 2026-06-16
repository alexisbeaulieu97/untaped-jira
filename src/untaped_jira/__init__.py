"""untaped-jira: manage Jira Data Center tickets, built on the untaped SDK.

``app`` and ``JiraClient`` are resolved lazily (PEP 562) so importing this
package never pulls in the CLI module (or the HTTP stack) until they are
actually used — ``__main__`` hands ``app`` to ``run_tool`` only when invoked.
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
    # cheap so the command tree never loads until ``app`` is accessed.
    if name == "app":
        from untaped_jira.cli import app  # noqa: PLC0415

        return app
    if name == "JiraClient":
        from untaped_jira.infrastructure import JiraClient  # noqa: PLC0415

        return JiraClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
