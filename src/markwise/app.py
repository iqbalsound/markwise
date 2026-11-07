import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from markwise import app_info as info
from markwise.db.models import User
from markwise.db.session import get_session, init_db
from markwise.paths import DB_PATH, ensure_data_dir
from markwise.ui.login import LoginDialog
from markwise.ui.main_window import MainWindow
from markwise.ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(info.APP_NAME)
    app.setOrganizationName(info.APP_NAME)
    app.setStyle("Fusion")
    apply_theme(app, QSettings().value("theme", "light", type=str))

    ensure_data_dir()
    init_db(DB_PATH)
    with get_session() as session:
        first_run = session.query(User).count() == 0

    login = LoginDialog(first_run=first_run)
    if not login.exec():
        return 0
    window = MainWindow(login.user)
    window.show()
    return app.exec()
