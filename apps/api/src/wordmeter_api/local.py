"""Local mode (desktop version): everything runs on the user's computer.

No account, no cloud: one implicit local user, data in a SQLite file inside the user's
application-data folder, and a server that only answers to this computer.
"""

import os
import secrets

# There are no sessions in local mode, but the shared code still expects a signing secret.
os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))

import asyncio  # noqa: E402
import uuid  # noqa: E402
from collections.abc import AsyncIterator, Iterator, Sequence  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import PlainTextResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from platformdirs import user_data_dir  # noqa: E402
from sqlalchemy import URL, Engine, create_engine, event, select  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from starlette.datastructures import Headers  # noqa: E402
from starlette.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402
from starlette.types import ASGIApp, Receive, Scope, Send  # noqa: E402

from wordmeter_api.config import settings  # noqa: E402
from wordmeter_api.db.base import Base, get_session  # noqa: E402
from wordmeter_api.db.models import User  # noqa: E402
from wordmeter_api.dependencies import SessionDep, get_current_user  # noqa: E402
from wordmeter_api.routers import analyze, auth, live, stats  # noqa: E402
from wordmeter_api.speech.transcriber import warm_up  # noqa: E402

DEFAULT_PORT = 8765
DEFAULT_ALLOWED_HOSTS = ("127.0.0.1", "localhost")
LOCAL_EMAIL = "local@wordmeter.local"


def default_data_dir() -> Path:
    """Where the user's data lives: the application-data folder of the operating system."""
    override = os.environ.get("WORDMETER_DATA_DIR")
    return Path(override) if override else Path(user_data_dir("Wordmeter", appauthor=False))


def create_local_engine(data_dir: Path) -> Engine:
    data_dir.mkdir(parents=True, exist_ok=True)
    url = URL.create("sqlite", database=str(data_dir / "wordmeter.db"))
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _configure(connection: Any, _record: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # readers do not block the writer
        cursor.execute("PRAGMA foreign_keys=ON")  # needed for ON DELETE CASCADE
        cursor.close()

    return engine


def _ensure_local_user(session_factory: "sessionmaker[Session]") -> uuid.UUID:
    with session_factory() as session:
        user = session.scalar(select(User).where(User.email == LOCAL_EMAIL))
        if user is None:
            # "!" is not a valid password hash: nobody can ever log in as this user.
            user = User(email=LOCAL_EMAIL, name="You", password_hash="!")
            session.add(user)
            session.commit()
        return user.id


class SameOriginGuard:
    """Turns away requests that come from another web site.

    A hostile page open in the browser could try to talk to the local server. Browsers say
    where a request comes from (the Origin header): anything but this very address is refused.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = Headers(scope=scope)
            origin = headers.get("origin")
            if origin is not None and urlparse(origin).netloc != headers.get("host", ""):
                if scope["type"] == "websocket":
                    await send({"type": "websocket.close", "code": 1008})
                else:
                    response = PlainTextResponse("Forbidden origin", status_code=403)
                    await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_local_app(
    data_dir: Path,
    web_dir: Path | None = None,
    allowed_hosts: Sequence[str] = DEFAULT_ALLOWED_HOSTS,
) -> FastAPI:
    engine = create_local_engine(data_dir)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    local_user_id = _ensure_local_user(session_factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.preload_models:
            await asyncio.to_thread(warm_up)
        yield
        engine.dispose()

    app = FastAPI(title="Wordmeter (local)", version="0.1.0", lifespan=lifespan)
    app.add_middleware(SameOriginGuard)
    # Also blocks "DNS rebinding": a hostile site pointing its own name at 127.0.0.1.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(allowed_hosts))

    def session_dependency() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    def local_user(session: SessionDep) -> User:
        user = session.get(User, local_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="Local user is missing")
        return user

    app.dependency_overrides[get_session] = session_dependency
    app.dependency_overrides[get_current_user] = local_user

    @app.get("/api/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local"}

    # Only what the local app needs from the auth routes: no signup, login or logout.
    app.add_api_route(
        "/api/auth/me", auth.me, methods=["GET"], response_model=auth.UserResponse, tags=["auth"]
    )
    app.add_api_route(
        "/api/auth/ws-ticket",
        auth.ws_ticket,
        methods=["POST"],
        response_model=auth.WsTicketResponse,
        tags=["auth"],
    )
    for router in (analyze.router, stats.router, live.router):
        app.include_router(router, prefix="/api")

    if web_dir is not None:
        # Mounted last: the API routes above take priority over the site's files.
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    return app


def main() -> None:
    port = int(os.environ.get("WORDMETER_PORT", DEFAULT_PORT))
    extra_hosts = [
        host.strip()
        for host in os.environ.get("WORDMETER_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]
    web = os.environ.get("WORDMETER_WEB_DIR")
    if web is not None and not Path(web).is_dir():
        raise SystemExit(f"WORDMETER_WEB_DIR does not exist: {web}")

    data_dir = default_data_dir()
    app = create_local_app(
        data_dir,
        web_dir=Path(web) if web else None,
        allowed_hosts=(*DEFAULT_ALLOWED_HOSTS, *extra_hosts),
    )
    print(f"Wordmeter (local) on http://127.0.0.1:{port} - data in {data_dir}")
    # Loopback only: other computers on the network cannot reach this server.
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
