from argon2 import PasswordHasher

from markwise.db.models import User

ph = PasswordHasher()


def create_user(session, username, password, role="teacher"):
    session.add(User(username=username, password_hash=ph.hash(password), role=role))


def verify(user, password) -> bool:
    try:
        return ph.verify(user.password_hash, password)
    except Exception:
        return False


def authenticate(session, username, password):
    """Return the User if the password is right, otherwise None."""
    user = session.query(User).filter_by(username=username).first()
    return user if user is not None and verify(user, password) else None
