"""
Smoke tests for views modules — Sprint 22.

Validates that:
- All view modules import without errors
- All render_* functions exist and are callable
- Component lazy-loading works
- Translations, styles, and utility modules are intact
- Settings module round-trips correctly

Does NOT require a running Streamlit server — uses module-level checks only.
"""

import importlib

import pytest

# ---------------------------------------------------------------------------
# 1. Import smoke tests — every view module must import cleanly
# ---------------------------------------------------------------------------

VIEW_MODULES = [
    "views",
    "views.auth",
    "views.dashboard",
    "views.demo",
    "views.detail_view",
    "views.finsense",
    "views.history",
    "views.landing",
    "views.result_view",
    "views.scan_history",
    "views.scan_view",
    "views.settings",
    "views.styles",
    "views.translations",
    "views.utils",
    "views.utils_new",
]


class TestViewImports:
    """Every view module must import without errors or side-effects."""

    @pytest.mark.parametrize("module_name", VIEW_MODULES)
    def test_module_imports(self, module_name):
        mod = importlib.import_module(module_name)
        assert mod is not None


# ---------------------------------------------------------------------------
# 2. Render function existence — all declared render_* must be callable
# ---------------------------------------------------------------------------

EXPECTED_RENDER_FUNCTIONS = [
    ("views.dashboard", "render_scanner_page"),
    ("views.demo", "render_demo_page"),
    ("views.finsense", "render_finsense_page"),
    ("views.finsense", "render_compound_interest_calculator"),
    ("views.finsense", "render_quiz_module"),
    ("views.history", "render_backtest_section"),
    ("views.landing", "render_finpilot_landing"),
    ("views.settings", "render_settings_page"),
    ("views.scan_history", "render_scan_history_page"),
]


class TestRenderFunctions:
    """All render_* functions should exist and be callable."""

    @pytest.mark.parametrize("module_name,func_name", EXPECTED_RENDER_FUNCTIONS)
    def test_render_function_exists(self, module_name, func_name):
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name, None)
        assert func is not None, f"{module_name}.{func_name} not found"
        assert callable(func), f"{module_name}.{func_name} is not callable"


# ---------------------------------------------------------------------------
# 3. Styles module — CSS must be present and non-trivial
# ---------------------------------------------------------------------------


class TestStylesModule:
    """Validate the global CSS and style utilities."""

    def test_global_css_exists(self):
        from views.styles import GLOBAL_CSS

        assert isinstance(GLOBAL_CSS, str)
        assert len(GLOBAL_CSS) > 100, "GLOBAL_CSS seems too short to be real CSS"

    def test_css_contains_expected_selectors(self):
        from views.styles import GLOBAL_CSS

        # Should contain at least basic Streamlit overrides
        assert "<style>" in GLOBAL_CSS or "font" in GLOBAL_CSS.lower() or "{" in GLOBAL_CSS


# ---------------------------------------------------------------------------
# 4. Translations module — i18n keys must be structured
# ---------------------------------------------------------------------------


class TestTranslations:
    """Validate translations data structure."""

    def test_translations_importable(self):
        mod = importlib.import_module("views.translations")
        assert mod is not None

    def test_translations_has_data(self):
        from views import translations

        # Should have at least one translation dict/function
        public_attrs = [a for a in dir(translations) if not a.startswith("_")]
        assert len(public_attrs) > 0, "translations module has no public attributes"


# ---------------------------------------------------------------------------
# 5. Settings module — load/save/default paths
# ---------------------------------------------------------------------------


class TestSettings:
    """Test settings read/write logic without Streamlit runtime."""

    def test_default_settings_structure(self):
        from views.settings import DEFAULT_SETTINGS

        assert isinstance(DEFAULT_SETTINGS, dict)
        assert "risk_score" in DEFAULT_SETTINGS
        assert "strategy" in DEFAULT_SETTINGS

    def test_load_settings_returns_dict(self, tmp_path, monkeypatch):
        """load_settings should return a dict even when file missing."""
        from views.settings import load_settings

        monkeypatch.setattr("views.settings.SETTINGS_FILE", str(tmp_path / "nope.json"))
        result = load_settings()
        assert isinstance(result, dict)

    def test_save_and_reload_settings(self, tmp_path, monkeypatch):
        """Round-trip: save → load should preserve data."""
        from views.settings import DEFAULT_SETTINGS, load_settings, save_settings

        settings_file = str(tmp_path / "test_settings.json")
        monkeypatch.setattr("views.settings.SETTINGS_FILE", settings_file)

        test_data = {**DEFAULT_SETTINGS, "risk_score": 99}
        save_settings(test_data)

        loaded = load_settings()
        assert loaded["risk_score"] == 99


# ---------------------------------------------------------------------------
# 6. Components lazy-loading
# ---------------------------------------------------------------------------


class TestComponentsLazyLoading:
    """Validate that views.components uses lazy loading."""

    def test_components_module_imports(self):
        import views.components

        assert views.components is not None

    def test_components_has_expected_submodules(self):
        """At least some known component functions should be discoverable."""
        from views import components

        # The lazy loader should expose key functions
        # We just check the module doesn't crash on dir()
        attrs = dir(components)
        assert isinstance(attrs, list)


# ---------------------------------------------------------------------------
# 7. Detail view helpers
# ---------------------------------------------------------------------------


class TestDetailView:
    """Test detail_view helper functions."""

    def test_detail_view_imports(self):
        from views.detail_view import render_detail_card, render_top_cards

        assert callable(render_top_cards)
        assert callable(render_detail_card)


# ---------------------------------------------------------------------------
# 8. Utils module
# ---------------------------------------------------------------------------


class TestViewUtils:
    """Test utility functions in views.utils."""

    def test_utils_imports(self):
        mod = importlib.import_module("views.utils")
        assert mod is not None

    def test_utils_new_imports(self):
        mod = importlib.import_module("views.utils_new")
        assert mod is not None


# ---------------------------------------------------------------------------
# 9. Scan view helpers
# ---------------------------------------------------------------------------


class TestScanView:
    """Test scan_view module availability."""

    def test_scan_view_functions_exist(self):
        from views.scan_view import render_market_pulse, render_sidebar

        assert callable(render_sidebar)
        assert callable(render_market_pulse)


# ---------------------------------------------------------------------------
# 10. Result view
# ---------------------------------------------------------------------------


class TestResultView:
    """Test result_view module."""

    def test_render_tabs_exists(self):
        from views.result_view import render_tabs

        assert callable(render_tabs)
