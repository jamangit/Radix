from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from wordmeter_api.config import settings

COOKIE_NAME = "access_token"

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _hasher.verify(password, hashed)


# Verified when the email is unknown, so response time does not reveal which emails exist.
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": user_id, "exp": expires}, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
