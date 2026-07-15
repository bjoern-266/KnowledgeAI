"""Tests for integration adapters, mode selection, and credential handling."""

from __future__ import annotations

import pytest

from acis.core.config import IntegrationMode, load_settings
from acis.core.errors import IntegrationUnavailableError, MissingCredentialError
from acis.integrations.base import build_integrations
from acis.integrations.canva.live import LiveCanva
from acis.integrations.canva.mock import MockCanva
from acis.integrations.interfaces import CanvaPort, TrendSourcePort
from acis.integrations.trends.factory import build_trends


def _mock_settings():
    return load_settings(
        env="development",
        overrides={"integrations": {"default_mode": "mock"}},
    )


def test_factory_returns_mock_by_default():
    trends = build_trends(IntegrationMode.MOCK, {})
    assert isinstance(trends, TrendSourcePort)
    result = trends.fetch_trends(limit=5)
    assert len(result) == 5
    assert all(t.source == "mock" for t in result)


def test_mock_trends_are_deterministic():
    a = build_trends(IntegrationMode.MOCK, {}).fetch_trends(region="de")
    b = build_trends(IntegrationMode.MOCK, {}).fetch_trends(region="de")
    assert [t.keyword for t in a] == [t.keyword for t in b]


def test_mode_selection_picks_live():
    live = build_trends(IntegrationMode.LIVE, {"api_key": "x"})
    assert live.is_live  # type: ignore[attr-defined]


def test_live_adapter_without_credentials_fails_setup():
    live = LiveCanva(config={})
    with pytest.raises(MissingCredentialError):
        live.setup()


def test_live_adapter_reports_missing_credentials_in_health():
    live = LiveCanva(config={})
    status = live.health_check()
    assert not status.healthy
    assert "api_key" in status.data["missing"]


def test_live_adapter_call_raises_unavailable():
    live = LiveCanva(config={"api_key": "x"})
    live.setup()  # credentials present -> setup ok
    with pytest.raises(IntegrationUnavailableError):
        live.export("design-1")


def test_mock_canva_satisfies_port():
    canva = MockCanva()
    assert isinstance(canva, CanvaPort)


def test_build_integrations_all_mock():
    bundle = build_integrations(_mock_settings())
    bundle.setup_all()
    try:
        assert all(a.mode is IntegrationMode.MOCK for a in bundle.adapters())
        assert all(a.health_check().healthy for a in bundle.adapters())
    finally:
        bundle.teardown_all()
