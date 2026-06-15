"""Console-script entrypoint for the ``untaped-jira`` CLI.

``untaped-jira`` is a standalone tool built on the untaped SDK: ``main()``
hands the Jira cyclopts app and a :class:`ToolSpec` to ``run_tool``, which
mounts the shared ``config`` / ``profile`` / ``skills`` groups, wires the
``--profile`` / ``--verbose`` root options, and runs under the SDK's error
contract.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from untaped.api import SkillAsset, ToolSpec, run_tool

from untaped_jira.cli import app
from untaped_jira.settings import JiraSettings

SPEC = ToolSpec(
    command="untaped-jira",
    section="jira",
    profile_model=JiraSettings,
    skills=(
        SkillAsset(
            name="untaped-jira",
            source=Path(str(files("untaped_jira").joinpath("skills", "untaped-jira"))),
            description="Use the untaped-jira CLI.",
        ),
    ),
)


def main() -> object:
    """Run the ``untaped-jira`` CLI."""
    return run_tool(app, SPEC)


if __name__ == "__main__":
    main()
