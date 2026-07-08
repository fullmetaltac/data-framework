from collections.abc import Iterator

import pytest
from sqlalchemy import Connection

from src.common.database import engine


@pytest.fixture
def db_connection() -> Iterator[Connection]:
    with engine.connect() as connection:
        yield connection
