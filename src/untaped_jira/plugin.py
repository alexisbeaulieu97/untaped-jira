"""Untaped plugin manifest for the Jira domain."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from untaped.api import CliSpec, PluginManifest, SkillSpec

from untaped_jira.settings import JiraSettings


class JiraPlugin:
    """Declare the Jira plugin's contributions to the untaped runtime."""

    id = "jira"
    untaped_api_version = 5

    def manifest(self) -> PluginManifest:
        """Describe the Jira CLI, settings section, and agent skill as data."""
        return PluginManifest(
            clis=(
                CliSpec(
                    name="jira",
                    import_path="untaped_jira.cli:app",
                    help="Manage Jira Data Center tickets from untaped.",
                ),
            ),
            profile_settings={"jira": JiraSettings},
            skills=(
                SkillSpec(
                    name="untaped-jira",
                    source=Path(str(files("untaped_jira").joinpath("skills", "untaped-jira"))),
                    description="Use the untaped Jira plugin.",
                ),
            ),
        )


plugin = JiraPlugin()
