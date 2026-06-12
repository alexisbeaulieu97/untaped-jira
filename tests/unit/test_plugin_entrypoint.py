"""Entry point and root-app integration checks for the Jira plugin."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError
from untaped.api import PluginManifest, PluginRegistry, get_config_section
from untaped.main import build_app
from untaped.plugins import register_plugins
from untaped.testing import CliInvoker

from untaped_jira.plugin import plugin as jira_plugin
from untaped_jira.settings import JiraSettings

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_jira_plugin_entry_point_is_declared() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    assert data["project"]["entry-points"]["untaped.plugins"]["jira"] == (
        "untaped_jira.plugin:plugin"
    )


def test_jira_plugin_declares_untaped_api_version() -> None:
    assert jira_plugin.untaped_api_version == 3


def test_jira_plugin_manifest_declares_all_contributions() -> None:
    manifest = jira_plugin.manifest()

    assert isinstance(manifest, PluginManifest)
    [cli] = manifest.clis
    assert cli.name == "jira"
    assert cli.app is None
    assert cli.import_path == "untaped_jira.cli:app"
    assert cli.help == "Manage Jira Data Center tickets from untaped."
    assert manifest.profile_settings == {"jira": JiraSettings}
    [skill] = manifest.skills
    assert skill.name == "untaped-jira"
    assert skill.description == "Use the untaped Jira plugin."
    assert skill.source.joinpath("SKILL.md").is_file()


def test_importing_plugin_module_does_not_import_cli_commands() -> None:
    probe = (
        "import sys\n"
        "import untaped_jira.plugin\n"
        "assert 'untaped_jira.cli.commands' not in sys.modules, 'CLI imported eagerly'\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_root_app_can_register_jira_plugin() -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliInvoker().invoke(app, ["jira", "--help"])

    assert result.exit_code == 0, result.output
    assert "Manage Jira Data Center tickets" in result.output


def test_jira_plugin_manifest_registers_cleanly() -> None:
    registry = PluginRegistry()

    register_plugins(registry, [jira_plugin])

    assert registry.load_errors == []
    assert registry.plugin_ids == {"jira"}
    assert "jira" in registry.lazy_clis
    assert registry.profile_sections["jira"] is JiraSettings
    spec = registry.skills["untaped-jira"]
    assert spec.description == "Use the untaped Jira plugin."
    assert spec.source.joinpath("SKILL.md").is_file()


def test_root_app_skills_list_includes_registered_jira_skill() -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliInvoker().invoke(app, ["skills", "list", "--format", "raw"])

    assert result.exit_code == 0, result.output
    assert "untaped-jira" in result.stdout.splitlines()


def test_config_list_includes_registered_jira_settings() -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliInvoker().invoke(app, ["config", "list", "--format", "raw", "--columns", "key"])

    assert result.exit_code == 0, result.output
    assert "jira.base_url" in result.stdout
    assert "jira.token" in result.stdout
    assert "jira.default_board_id" in result.stdout
    assert "jira.assigned_jql" in result.stdout


def test_config_list_redacts_jira_token(jira_config: Path) -> None:
    app = build_app(plugins=[jira_plugin])

    result = CliInvoker().invoke(
        app, ["config", "list", "--format", "raw", "--columns", "key", "--columns", "value"]
    )

    assert result.exit_code == 0, result.output
    assert "jira_pat" not in result.stdout
    assert "jira.token\t***" in result.stdout


def test_jira_token_can_be_loaded_from_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = tmp_path / "config.yml"
    cfg.write_text("jira:\n  base_url: https://jira.example.com\n")
    monkeypatch.setenv("UNTAPED_CONFIG", str(cfg))
    monkeypatch.setenv("UNTAPED_JIRA__TOKEN", "from-env")
    build_app(plugins=[jira_plugin])

    settings = get_config_section("jira", JiraSettings)

    assert settings.token is not None
    assert settings.token.get_secret_value() == "from-env"


def test_jira_settings_reject_blank_assigned_jql() -> None:
    with pytest.raises(ValidationError, match="assigned_jql must not be blank"):
        JiraSettings(assigned_jql="   ")
