"""Shared pytest fixtures: isolated untaped settings plus a Jira config file."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from untaped import get_settings
from untaped.settings import register_profile_settings, reset_config_registry_for_tests

from untaped_jira.settings import JiraSettings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    reset_config_registry_for_tests()
    # Tests invoke the jira app directly, which skips run_tool's section
    # registration, so mirror the tool's profile-settings contribution
    # (idempotent for the same model class) for plugin_context().section(
    # "jira", ...) to resolve.
    register_profile_settings("jira", JiraSettings)
    get_settings.cache_clear()
    yield
    reset_config_registry_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def jira_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cfg = tmp_path / "config.yml"
    cfg.write_text("jira:\n  base_url: https://jira.example.com\n  token: jira_pat\n")
    monkeypatch.setenv("UNTAPED_CONFIG", str(cfg))
    return cfg
