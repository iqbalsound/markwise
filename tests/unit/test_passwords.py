from markwise.auth.passwords import authenticate, create_user
from markwise.db.session import get_session


def test_login_right_and_wrong_password(db):
    with get_session() as s:
        create_user(s, "teacher", "secret123")
    with get_session() as s:
        assert authenticate(s, "teacher", "secret123") is not None
        assert authenticate(s, "teacher", "wrong") is None
        assert authenticate(s, "nobody", "secret123") is None
