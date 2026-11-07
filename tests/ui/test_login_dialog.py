from PySide6.QtCore import Qt

from markwise.auth.passwords import create_user
from markwise.db.session import get_session
from markwise.ui.login import LoginDialog


def test_wrong_password_is_rejected(qtbot, db):
    with get_session() as s:
        create_user(s, "teacher", "secret123")
    dialog = LoginDialog(first_run=False)
    qtbot.addWidget(dialog)
    dialog.username.setText("teacher")
    dialog.password.setText("wrong")
    qtbot.mouseClick(dialog.login_button, Qt.MouseButton.LeftButton)
    assert "Invalid" in dialog.error_label.text()
    assert dialog.user is None


def test_right_password_logs_in(qtbot, db):
    with get_session() as s:
        create_user(s, "teacher", "secret123")
    dialog = LoginDialog(first_run=False)
    qtbot.addWidget(dialog)
    dialog.username.setText("teacher")
    dialog.password.setText("secret123")
    qtbot.mouseClick(dialog.login_button, Qt.MouseButton.LeftButton)
    assert dialog.user is not None and dialog.user.username == "teacher"


def test_first_run_creates_admin(qtbot, db):
    dialog = LoginDialog(first_run=True)
    qtbot.addWidget(dialog)
    dialog.username.setText("boss")
    dialog.password.setText("longpassword")
    dialog.confirm.setText("longpassword")
    qtbot.mouseClick(dialog.login_button, Qt.MouseButton.LeftButton)
    assert dialog.user is not None and dialog.user.role == "admin"
