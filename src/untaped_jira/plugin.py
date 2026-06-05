"""Untaped plugin registration for the Jira domain."""

from __future__ import annotations

from untaped.plugins import PluginRegistry

from untaped_jira import app
from untaped_jira.settings import JiraSettings


class JiraPlugin:
    """Register Jira settings and commands with the untaped runtime."""

    id = "jira"

    def register(self, registry: PluginRegistry) -> None:
        registry.add_profile_settings("jira", JiraSettings)
        registry.add_cli("jira", app)


plugin = JiraPlugin()
