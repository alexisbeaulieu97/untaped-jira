"""Untaped plugin registration for the Jira domain."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from untaped.plugins import PluginRegistry, SkillSpec

from untaped_jira import app
from untaped_jira.settings import JiraSettings


class JiraPlugin:
    """Register Jira settings and commands with the untaped runtime."""

    id = "jira"
    untaped_api_version = 2

    def register(self, registry: PluginRegistry) -> None:
        registry.add_profile_settings("jira", JiraSettings)
        registry.add_cli("jira", app)
        registry.add_skill(
            SkillSpec(
                name="untaped-jira",
                source=Path(str(files("untaped_jira").joinpath("skills", "untaped-jira"))),
                description="Use the untaped Jira plugin.",
            )
        )


plugin = JiraPlugin()
