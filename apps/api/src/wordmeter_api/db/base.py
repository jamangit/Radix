from collections.abc import Iterator
from functools import cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from wordmeter_api.config import settings


class Base(DeclarativeBase):
    pass


@cache
def _session_factory() -> "sessionmaker[Session]":
    # Created on first use, so the desktop version never needs the PostgreSQL driver.
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return sessionmaker(engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    with _session_factory()() as session:
        yield session
