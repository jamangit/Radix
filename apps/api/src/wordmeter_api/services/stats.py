import calendar
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from wordmeter_api.analysis import WordCount
from wordmeter_api.db.models import Analysis, AnalysisWord

Period = Literal["day", "month", "year"]
TOP_WORDS_LIMIT = 10


class SeriesPoint(BaseModel):
    label: str
    words: int


class StatsResponse(BaseModel):
    period: Period
    total_words: int
    analyses: int
    vocabulary_size: int
    elapsed_days: int
    words_per_day: float
    top_words: list[WordCount]
    series: list[SeriesPoint]


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def period_bounds(
    period: Period, tz: ZoneInfo, now: datetime | None = None
) -> tuple[datetime, datetime]:
    """Start (inclusive) and end (exclusive) of the current period, in the user's timezone."""
    local_now = (now or datetime.now(tz)).astimezone(tz)
    midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "day":
        start = midnight
        end = start + timedelta(days=1)
    elif period == "month":
        start = midnight.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
    else:
        start = midnight.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
    return start, end


def count_elapsed_days(
    start: datetime, account_created_at: datetime, now: datetime, tz: ZoneInfo
) -> int:
    """Days elapsed in the period, today included, counted from sign-up for newer accounts."""
    signup_day = _as_utc(account_created_at).astimezone(tz).date()
    first_day = max(start.date(), signup_day)
    return max((now.astimezone(tz).date() - first_day).days + 1, 1)


def _slots(period: Period, start: datetime) -> list[tuple[int, str]]:
    if period == "day":
        return [(hour, f"{hour:02d}:00") for hour in range(24)]
    if period == "month":
        days = calendar.monthrange(start.year, start.month)[1]
        return [(day, str(day)) for day in range(1, days + 1)]
    return [(month, calendar.month_abbr[month]) for month in range(1, 13)]


def _slot_key(period: Period, local: datetime) -> int:
    if period == "day":
        return local.hour
    if period == "month":
        return local.day
    return local.month


def get_stats(
    session: Session,
    user_id: uuid.UUID,
    period: Period,
    tz: ZoneInfo,
    account_created_at: datetime,
    now: datetime | None = None,
) -> StatsResponse:
    local_now = (now or datetime.now(tz)).astimezone(tz)
    start, end = period_bounds(period, tz, now=local_now)
    in_period = (
        Analysis.user_id == user_id,
        Analysis.created_at >= start.astimezone(UTC),
        Analysis.created_at < end.astimezone(UTC),
    )

    rows = session.execute(
        select(Analysis.created_at, Analysis.total_words).where(*in_period)
    ).all()
    words_per_slot: dict[int, int] = {}
    for created_at, total in rows:
        key = _slot_key(period, _as_utc(created_at).astimezone(tz))
        words_per_slot[key] = words_per_slot.get(key, 0) + total

    vocabulary = (
        session.scalar(
            select(func.count(distinct(AnalysisWord.word)))
            .select_from(AnalysisWord)
            .join(Analysis, Analysis.id == AnalysisWord.analysis_id)
            .where(*in_period)
        )
        or 0
    )

    total_count = func.sum(AnalysisWord.count)
    top = session.execute(
        select(AnalysisWord.word, total_count.label("total"))
        .join(Analysis, Analysis.id == AnalysisWord.analysis_id)
        .where(*in_period)
        .group_by(AnalysisWord.word)
        .order_by(total_count.desc(), AnalysisWord.word)
        .limit(TOP_WORDS_LIMIT)
    ).all()

    total_words = sum(words_per_slot.values())
    elapsed_days = count_elapsed_days(start, account_created_at, local_now, tz)

    return StatsResponse(
        period=period,
        total_words=total_words,
        analyses=len(rows),
        vocabulary_size=vocabulary,
        elapsed_days=elapsed_days,
        words_per_day=round(total_words / elapsed_days, 1),
        top_words=[WordCount(word=word, count=int(total)) for word, total in top],
        series=[
            SeriesPoint(label=label, words=words_per_slot.get(key, 0))
            for key, label in _slots(period, start)
        ],
    )
