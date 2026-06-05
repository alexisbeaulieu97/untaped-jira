from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from untaped import get_settings
from untaped.settings import reset_config_registry_for_tests


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    reset_config_registry_for_tests()
    get_settings.cache_clear()
    yield
    os.environ.pop("UNTAPED_PROFILE", None)
    reset_config_registry_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def jira_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cfg = tmp_path / "config.yml"
    cfg.write_text(
        "profiles:\n"
        "  default:\n"
        "    jira:\n"
        "      base_url: https://jira.example.com\n"
        "      token: jira_pat\n"
    )
    monkeypatch.setenv("UNTAPED_CONFIG", str(cfg))
    monkeypatch.delenv("UNTAPED_PROFILE", raising=False)
    return cfg
