"""
Integration tests for views module — Sprint 3 F1.

Tests that view modules import correctly and expose expected interfaces.
Does NOT require a running Streamlit server.
"""

import importlib
import json
import os
import sys

import pytest


class TestViewModuleImports:
    """Verify all view modules can be imported without side-effects."""

    VIEW_MODULES = [
        "views.dashboard",
        "views.demo",
        "views.finsense",
        "views.history",
        "views.landing",
        "views.settings",
        "views.styles",
        "views.translations",
        "views.utils",
    ]

    @pytest.mark.parametrize("module_name", VIEW_MODULES)
    def test_import_succeeds(self, module_name):
        """Each view module should import without error."""
        mod = importlib.import_module(module_name)
        assert mod is not None


class TestSettingsModule:
    """Tests for views.settings utilities (non-Streamlit parts)."""

    def test_default_settings_structure(self):
        from views.settings import DEFAULT_SETTINGS

        assert isinstance(DEFAULT_SETTINGS, dict)
        assert "risk_score" in DEFAULT_SETTINGS
        assert "strategy" in DEFAULT_SETTINGS
        assert "market" in DEFAULT_SETTINGS

    def test_load_settings_returns_dict(self, tmp_path, monkeypatch):
        """load_settings should return a dict even if file is missing."""
        from views import settings as s

        fake_path = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr(s, "SETTINGS_FILE", fake_path)
        result = s.load_settings()
        assert isinstance(result, dict)

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        """Settings saved to disk should be loadable."""
        from views import settings as s

        fake_path = str(tmp_path / "settings.json")
        monkeypatch.setattr(s, "SETTINGS_FILE", fake_path)
        test_data = {"risk_score": 7, "strategy": "Agresif", "market": "US"}
        s.save_settings(test_data)
        loaded = s.load_settings()
        assert loaded["risk_score"] == 7
        assert loaded["strategy"] == "Agresif"


class TestTranslationsModule:
    """Tests for views.translations."""

    def test_translations_dict_exists(self):
        from views.translations import TRANSLATIONS

        assert isinstance(TRANSLATIONS, dict)
        assert "tr" in TRANSLATIONS or "en" in TRANSLATIONS

    def test_t_function_returns_string(self):
        """t() helper should always return a string."""
        try:
            from views.translations import t

            result = t("app_title")
            assert isinstance(result, str)
        except ImportError:
            pytest.skip("t() not available")


class TestDictionaryData:
    """Tests for data/dictionary.json integrity."""

    DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dictionary.json")

    @pytest.mark.skipif(
        not os.path.exists(
            os.path.join(os.path.dirname(__file__), "..", "data", "dictionary.json")
        ),
        reason="dictionary.json not found",
    )
    def test_dictionary_is_valid_json(self):
        with open(self.DICT_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, (dict, list))

    @pytest.mark.skipif(
        not os.path.exists(
            os.path.join(os.path.dirname(__file__), "..", "data", "dictionary.json")
        ),
        reason="dictionary.json not found",
    )
    def test_dictionary_entries_have_required_fields(self):
        """Each entry should have at minimum a definition/description."""
        with open(self.DICT_PATH, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            # dict keyed by term
            for term, entry in list(data.items())[:10]:
                assert isinstance(entry, (str, dict)), f"Bad entry for {term}"
        elif isinstance(data, list):
            for entry in data[:10]:
                assert isinstance(entry, dict)
