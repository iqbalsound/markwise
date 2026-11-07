from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from markwise.db.models import Base

_engine = None
_Session = None


def init_db(path) -> None:
    """Open (and create if needed) the database. Use ':memory:' for tests."""
    global _engine, _Session
    if str(path) == ":memory:":
        _engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    else:
        _engine = create_engine(f"sqlite:///{path}", connect_args={"timeout": 30})
    Base.metadata.create_all(_engine)
    _Session = sessionmaker(_engine, expire_on_commit=False)


@contextmanager
def get_session():
    """Use as: with get_session() as s: ...   (commits on success, rolls back on error)"""
    session = _Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
