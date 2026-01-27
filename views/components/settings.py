# -*- coding: utf-8 -*-
"""
FinPilot Settings Card
======================
SettingsCard React bileşenini Streamlit'te gösterme.
"""

import re
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


@lru_cache(maxsize=1)
def load_settingscard_markup() -> tuple[str | None, str | None]:
    """Load the compiled SettingsCard bundle and inline CSS/JS for Streamlit."""
    dist_dir = Path(__file__).resolve().parent.parent.parent / "SettingsCard" / "dist"
    index_path = dist_dir / "index.html"
    if not index_path.exists():
        return None, "SettingsCard derlemesi bulunamadı. Lütfen önce Vite build çalıştırın."

    html = index_path.read_text(encoding="utf-8")
    css_match = re.search(r'href="(?P<href>[^\"]+\.css)"', html)
    js_match = re.search(r'src="(?P<src>[^\"]+\.js)"', html)

    if js_match is None:
        return None, "SettingsCard index.html içinde JS kaynağı bulunamadı."

    css_content = ""
    if css_match:
        css_path = dist_dir / css_match.group("href").lstrip("/")
        if css_path.exists():
            css_content = css_path.read_text(encoding="utf-8").replace("</style", "<\\/style")

    js_path = dist_dir / js_match.group("src").lstrip("/")
    if not js_path.exists():
        return None, f"JS asset eksik: {js_path.name}"

    js_content = js_path.read_text(encoding="utf-8").replace("</script", "<\\/script")

    markup = f"""<!doctype html>
<html lang=\"tr\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <style>{css_content}</style>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\">{js_content}</script>
  </body>
</html>"""
    return markup, None


def render_settings_card(height: int = 860) -> None:
    """Render the SettingsCard React bundle or show a helpful warning."""
    markup, error = load_settingscard_markup()
    if error:
        st.warning(error)
        st.info(
            "`SettingsCard/dist/` içeriğini oluşturmak için projede `npm run build` çalıştırın."
        )
        return

    if not markup:
        st.warning("SettingsCard içeriği yüklenemedi.")
        return

    components.html(markup, height=height, scrolling=True)
