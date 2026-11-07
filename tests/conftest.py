import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # tests run without a screen

import pytest

from markwise.db.session import init_db


@pytest.fixture
def db():
    init_db(":memory:")
