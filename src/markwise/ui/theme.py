from PySide6.QtCore import Qt

from markwise.paths import resource_path


def apply_theme(app, mode: str) -> str:
    """mode: 'light', 'dark' or 'system'. Returns the theme actually applied."""
    if mode == "system":
        try:
            dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        except AttributeError:
            dark = False
        mode = "dark" if dark else "light"
    if mode not in ("light", "dark"):
        mode = "light"
    qss = resource_path("assets", "themes", f"{mode}.qss").read_text(encoding="utf-8")
    app.setStyleSheet(qss)
    return mode
