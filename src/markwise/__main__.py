import os
import sys
import tempfile
import traceback
from pathlib import Path


def selftest() -> int:
    """Used by the tests and the build: checks the app can start and all libraries load. Exit 0 = OK."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        import argon2  # noqa: F401
        import docx  # noqa: F401
        import google.genai  # noqa: F401
        import keyring  # noqa: F401
        import openpyxl  # noqa: F401
        import pandas  # noqa: F401
        import pymupdf  # noqa: F401
        from PySide6 import QtPdf, QtPdfWidgets  # noqa: F401
        from PySide6.QtWidgets import QApplication

        from markwise.db.session import init_db
        from markwise.ui.theme import apply_theme

        app = QApplication([])
        init_db(":memory:")
        for mode in ("light", "dark"):
            apply_theme(app, mode)
        return 0
    except Exception:
        # A Windows windowed build has no console, so write the error to a file as well.
        (Path(tempfile.gettempdir()) / "markwise_selftest.log").write_text(traceback.format_exc())
        traceback.print_exc()
        return 1


def run() -> None:
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    from markwise.app import main

    sys.exit(main())


if __name__ == "__main__":
    run()
