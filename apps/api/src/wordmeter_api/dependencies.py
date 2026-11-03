import uuid
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from wordmeter_api.db.base import get_session
from wordmeter_api.db.models import User
from wordmeter_api.security import COOKIE_NAME, decode_access_token

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(
    session: SessionDep,
    access_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    if access_token is None:
        raise unauthorized
    subject = decode_access_token(access_token)
    if subject is None:
        raise unauthorized
    try:
        user = session.get(User, uuid.UUID(subject))
    except ValueError:
        raise unauthorized from None
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
