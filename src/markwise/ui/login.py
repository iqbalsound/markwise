from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from markwise import app_info as info
from markwise.auth.passwords import authenticate, create_user
from markwise.db.session import get_session


class LoginDialog(QDialog):
    """Login window. With first_run=True it creates the first (admin) account instead."""

    def __init__(self, first_run: bool = False, parent=None):
        super().__init__(parent)
        self.first_run = first_run
        self.user = None
        self.setWindowTitle(f"{info.APP_NAME} - " + ("Create admin account" if first_run else "Login"))
        self.setMinimumWidth(380)

        heading = QLabel(f"<h2>{info.APP_NAME}</h2><p>"
                         + ("Create the administrator account." if first_run else "Please sign in.") + "</p>")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Repeat password")
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm.setVisible(first_run)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #d64545;")
        self.login_button = QPushButton("Create admin account" if first_run else "Login")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.submit)

        layout = QVBoxLayout(self)
        for widget in (heading, self.username, self.password, self.confirm, self.error_label, self.login_button):
            layout.addWidget(widget)

    def submit(self):
        name = self.username.text().strip()
        password = self.password.text()
        if not name or not password:
            self.error_label.setText("Enter a username and password.")
            return
        if self.first_run:
            if len(password) < 8:
                self.error_label.setText("Password must be at least 8 characters.")
                return
            if password != self.confirm.text():
                self.error_label.setText("Passwords do not match.")
                return
            with get_session() as session:
                create_user(session, name, password, role="admin")
        with get_session() as session:
            user = authenticate(session, name, password)
        if user is None:
            self.error_label.setText("Invalid username or password.")
            return
        self.user = user
        self.accept()
