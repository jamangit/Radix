from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query, status

from wordmeter_api.dependencies import CurrentUser, SessionDep
from wordmeter_api.services.stats import Period, StatsResponse, get_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def read_stats(
    user: CurrentUser,
    session: SessionDep,
    period: Period = "day",
    timezone: Annotated[str, Query(max_length=64)] = "UTC",
) -> StatsResponse:
    try:
        tz = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown timezone") from None
    return get_stats(session, user.id, period, tz, user.created_at)
