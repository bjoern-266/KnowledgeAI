"""Tests for the layered configuration system."""

from __future__ import annotations

import pytest

from acis.core.config import IntegrationMode, StorageBackend, load_settings
from acis.core.errors import ConfigError


def test_defaults_load():
    settings = load_settings(env="development")
    assert settings.app_name == "ACIS"
    assert settings.env == "development"
    assert settings.quality.min_score == pytest.approx(0.75)


def test_env_layer_overrides_default():
    dev = load_settings(env="development")
    prod = load_settings(env="production")
    # production.yaml raises the quality threshold and flips default mode.
    assert prod.quality.min_score > dev.quality.min_score
    assert prod.integrations.default_mode is IntegrationMode.LIVE


def test_overrides_applied_last():
    settings = load_settings(
        env="development",
        overrides={"storage": {"backend": "memory"}},
    )
    assert settings.storage.backend is StorageBackend.MEMORY


def test_integration_mode_inheritance():
    settings = load_settings(
        env="development",
        overrides={
            "integrations": {
                "default_mode": "mock",
                "canva": {"mode": "live"},
            }
        },
    )
    assert settings.integrations.resolve_mode("canva") is IntegrationMode.LIVE
    assert settings.integrations.resolve_mode("tiktok") is IntegrationMode.MOCK


def test_env_var_reads_secret(monkeypatch):
    monkeypatch.setenv("ACIS_INTEGRATIONS__OPENAI__API_KEY", "secret-123")
    settings = load_settings(env="development")
    assert settings.integrations.openai.model_dump().get("api_key") == "secret-123"


def test_settings_are_frozen():
    from pydantic import ValidationError as PydanticValidationError

    settings = load_settings(env="development")
    with pytest.raises(PydanticValidationError):
        settings.app_name = "changed"  # type: ignore[misc]


def test_invalid_env_file_is_config_error(tmp_path):
    (tmp_path / "default.yaml").write_text(":\n  - not valid mapping root", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_settings(env="development", config_dir=tmp_path)
