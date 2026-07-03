"""Verify config/settings.json contains all required feature-gate keys."""
import json
from pathlib import Path


def test_settings_has_evolution_budget():
    data = json.loads(Path("config/settings.json").read_text())
    assert data.get("evolution_budget_tokens") == 200000


def test_settings_has_auto_evolution_nightly():
    data = json.loads(Path("config/settings.json").read_text())
    assert data.get("auto_evolution_nightly") is False


def test_settings_has_auto_plaza_sustainability_topics():
    data = json.loads(Path("config/settings.json").read_text())
    assert data.get("auto_plaza_sustainability_topics") is True


def test_settings_has_trigger_daemon_enabled():
    data = json.loads(Path("config/settings.json").read_text())
    assert data.get("trigger_daemon_enabled") is False


def test_settings_has_enforce_relationship_gate():
    data = json.loads(Path("config/settings.json").read_text())
    assert data.get("enforce_relationship_gate") is False


def test_settings_has_auto_extract_on_consensus():
    data = json.loads(Path("config/settings.json").read_text())
    assert data.get("auto_extract_on_consensus") is True
