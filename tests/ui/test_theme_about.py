from markwise import app_info
from markwise.ui.theme import apply_theme


def test_both_themes_load(qapp):
    assert apply_theme(qapp, "light") == "light"
    light = qapp.styleSheet()
    assert apply_theme(qapp, "dark") == "dark"
    assert qapp.styleSheet() != light
    assert apply_theme(qapp, "system") in ("light", "dark")


def test_identity():
    assert app_info.APP_VERSION == "1.0.0"
    assert app_info.APP_NAME == "MarkWise"
