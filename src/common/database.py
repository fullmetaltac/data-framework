from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SessionType
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session() -> Generator[SessionType, None, None]:
    session = Session()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
