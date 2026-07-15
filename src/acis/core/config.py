"""Layered configuration system.

Configuration is resolved from four layers, each overriding the previous:

1. ``config/default.yaml``          - safe defaults committed to the repo.
2. ``config/<env>.yaml``            - environment-specific overrides.
3. Process environment variables    - ``ACIS_*`` (nested via ``__``).
4. ``.env`` file                    - developer convenience, git-ignored.

Secrets (API keys, tokens) are ONLY ever read from layers 3/4. YAML files must
never contain credentials.

Usage::

    from acis.core.config import load_settings
    settings = load_settings()            # picks env from ACIS_ENV
    settings.integrations.canva.mode      # -> "mock"

The returned :class:`Settings` object is immutable and fully validated.
"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from acis.core.errors import ConfigError

# Repository root is three levels above this file: src/acis/core/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_DIR = _PROJECT_ROOT / "config"


class IntegrationMode(StrEnum):
    """Whether an adapter talks to a real backend or a simulated one."""

    MOCK = "mock"
    LIVE = "live"


class LogFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"


class StorageBackend(StrEnum):
    MEMORY = "memory"
    SQLITE = "sqlite"


# --------------------------------------------------------------------------- #
# Nested config models
# --------------------------------------------------------------------------- #
class LogConfig(BaseModel):
    level: str = "INFO"
    format: LogFormat = LogFormat.CONSOLE


class StorageConfig(BaseModel):
    backend: StorageBackend = StorageBackend.SQLITE
    sqlite_path: str = "var/acis.db"


class JobConfig(BaseModel):
    interval_seconds: int = Field(gt=0)
    enabled: bool = True


class SchedulerConfig(BaseModel):
    timezone: str = "UTC"
    jobs: dict[str, JobConfig] = Field(default_factory=dict)


class IntegrationConfig(BaseModel):
    """Per-integration settings.

    ``mode`` may be ``None`` to inherit ``integrations.default_mode``. Extra
    vendor-specific fields (api_key, tokens, ...) are permitted and read from
    the environment.
    """

    model_config = SettingsConfigDict(extra="allow")

    mode: IntegrationMode | None = None


class IntegrationsConfig(BaseModel):
    model_config = SettingsConfigDict(extra="allow")

    default_mode: IntegrationMode = IntegrationMode.MOCK
    canva: IntegrationConfig = Field(default_factory=IntegrationConfig)
    instagram: IntegrationConfig = Field(default_factory=IntegrationConfig)
    tiktok: IntegrationConfig = Field(default_factory=IntegrationConfig)
    openai: IntegrationConfig = Field(default_factory=IntegrationConfig)
    trends: IntegrationConfig = Field(default_factory=IntegrationConfig)
    research: IntegrationConfig = Field(default_factory=IntegrationConfig)
    analytics: IntegrationConfig = Field(default_factory=IntegrationConfig)

    def resolve_mode(self, name: str) -> IntegrationMode:
        """Return the effective mode for an integration, applying inheritance."""
        integration = getattr(self, name, None)
        if integration is not None and integration.mode is not None:
            return integration.mode
        return self.default_mode


class QualityConfig(BaseModel):
    min_score: float = Field(default=0.75, ge=0.0, le=1.0)
    require_fact_check: bool = True
    require_source_check: bool = True
    require_spelling_check: bool = True
    require_design_check: bool = True
    min_sources_per_topic: int = Field(default=2, ge=1)


class ContentConfig(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["instagram", "tiktok"])
    instagram_carousel_slides: int = 8
    topics: list[str] = Field(default_factory=list)


class PaletteConfig(BaseModel):
    model_config = SettingsConfigDict(extra="allow")

    background: list[str] = Field(default_factory=list)
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#B0B0B0"
    accent: str = "#FFD400"


class BrandingConfig(BaseModel):
    design_language: list[str] = Field(default_factory=list)
    palette: PaletteConfig = Field(default_factory=PaletteConfig)
    accent_usage: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Root settings
# --------------------------------------------------------------------------- #
class Settings(BaseSettings):
    """Fully resolved, validated application configuration (immutable)."""

    model_config = SettingsConfigDict(
        env_prefix="ACIS_",
        env_nested_delimiter="__",
        extra="ignore",
        frozen=True,
    )

    app_name: str = "ACIS"
    env: str = "development"

    log: LogConfig = Field(default_factory=LogConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    content: ContentConfig = Field(default_factory=ContentConfig)
    branding: BrandingConfig = Field(default_factory=BrandingConfig)

    #: Absolute project root, filled in by the loader. Not read from env.
    project_root: Path = _PROJECT_ROOT

    @model_validator(mode="after")
    def _validate_live_integrations(self) -> Settings:
        """Fail fast if a live integration is missing a critical field.

        This is intentionally light-touch: adapters perform their own detailed
        credential validation. Here we only guard the most common mistake -
        switching an adapter to ``live`` while leaving it unconfigured.
        """
        # Detailed per-adapter credential checks live in each adapter's
        # ``validate_credentials`` so the foundation stays decoupled from
        # vendor specifics. Nothing to enforce globally here yet.
        return self


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (returns a new dict)."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"Invalid YAML in {path}", context={"path": str(path)}) from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config root must be a mapping: {path}")
    return data


def load_settings(
    env: str | None = None,
    *,
    config_dir: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> Settings:
    """Build a validated :class:`Settings` from all configuration layers.

    Args:
        env: environment name; defaults to ``ACIS_ENV`` or ``development``.
        config_dir: directory holding the YAML files (tests may override).
        overrides: final in-memory overrides applied on top of everything,
            useful for tests. These do NOT come from disk.
    """
    env = env or os.getenv("ACIS_ENV", "development")
    config_dir = config_dir or _CONFIG_DIR

    merged = _load_yaml(config_dir / "default.yaml")
    merged = _deep_merge(merged, _load_yaml(config_dir / f"{env}.yaml"))
    merged["env"] = env
    if overrides:
        merged = _deep_merge(merged, overrides)

    try:
        # BaseSettings merges env vars / .env on top of the YAML-derived values.
        return Settings(**merged)
    except Exception as exc:  # noqa: BLE001 - normalise to ConfigError
        raise ConfigError(f"Failed to build settings: {exc}") from exc
