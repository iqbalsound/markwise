from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QLabel, QVBoxLayout
from markwise.auth.passwords import verify
from markwise.db.models import User
from markwise.db.session import get_session

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login")
        self.error_label = QLabel("")
        layout = QVBoxLayout(self)
        for w in (self.username, self.password, self.login_button, self.error_label):
            layout.addWidget(w)
        self.login_button.clicked.connect(self.try_login)

    def try_login(self):
        with get_session() as session:
            user = session.query(User).filter_by(username=self.username.text()).first()
            if user and verify(user, self.password.text()):
                self.error_label.setText("")
                self.accept_user(user)       # open the main window
            else:
                self.error_label.setText("Invalid username or password")
