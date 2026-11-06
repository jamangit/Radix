from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from wordmeter_api.config import settings

COOKIE_NAME = "access_token"
WS_TICKET_TYPE = "ws"

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _hasher.verify(password, hashed)


# Verified when the email is unknown, so response time does not reveal which emails exist.
DUMMY_HASH = hash_password("not-a-real-password")


def _decode(token: str) -> dict[str, object] | None:
    try:
        payload: dict[str, object] = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return payload


def create_access_token(user_id: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": user_id, "exp": expires}, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> str | None:
    payload = _decode(token)
    # Session tokens carry no "typ": a short-lived ticket must never work as a session.
    if payload is None or "typ" in payload:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None


def create_ws_ticket(user_id: str) -> str:
    """Short-lived, single-purpose token used to open a WebSocket on a different origin."""
    expires = datetime.now(UTC) + timedelta(seconds=settings.ws_ticket_seconds)
    claims = {"sub": user_id, "typ": WS_TICKET_TYPE, "exp": expires}
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def decode_ws_ticket(token: str) -> str | None:
    payload = _decode(token)
    if payload is None or payload.get("typ") != WS_TICKET_TYPE:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
