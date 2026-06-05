"""Entry point and root-app integration checks for the Jira plugin."""

from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner
from untaped.main import build_app

from untaped_jira.plugin import plugin as jira_plugin

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_jira_plugin_entry_point_is_declared() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    assert data["project"]["entry-points"]["untaped.plugins"]["jira"] == (
        "untaped_jira.plugin:plugin"
    )


def test_root_app_can_register_jira_plugin() -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliRunner().invoke(app, ["jira", "--help"])

    assert result.exit_code == 0, result.output
    assert "Manage Jira Data Center tickets" in result.output


def test_config_list_includes_registered_jira_settings() -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliRunner().invoke(app, ["config", "list", "--format", "raw", "--columns", "key"])

    assert result.exit_code == 0, result.output
    assert "jira.base_url" in result.stdout
    assert "jira.token" in result.stdout
    assert "jira.default_board_id" in result.stdout


def test_config_list_redacts_jira_token(jira_config: Path) -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliRunner().invoke(
        app, ["config", "list", "--format", "raw", "--columns", "key", "--columns", "value"]
    )

    assert result.exit_code == 0, result.output
    assert "jira_pat" not in result.stdout
    assert "jira.token\t***" in result.stdout
