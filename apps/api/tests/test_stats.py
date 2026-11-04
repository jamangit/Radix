from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from wordmeter_api.services.stats import count_elapsed_days, period_bounds


def test_analyze_requires_authentication(client: TestClient) -> None:
    assert client.post("/analyze", json={"text": "bonjour"}).status_code == 401


def test_stats_require_authentication(client: TestClient) -> None:
    assert client.get("/stats").status_code == 401


def test_stats_sum_up_the_analyses_of_the_day(auth_client: TestClient) -> None:
    auth_client.post("/analyze", json={"text": "Le chat mange. Le chat dort.", "language": "fr"})
    auth_client.post("/analyze", json={"text": "Le chien dort.", "language": "fr"})

    response = auth_client.get("/stats", params={"period": "day"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_words"] == 9
    assert body["analyses"] == 2
    assert body["vocabulary_size"] >= 3
    assert body["top_words"][0] == {"word": "chat", "count": 2}
    assert len(body["series"]) == 24
    assert sum(point["words"] for point in body["series"]) == 9


def test_stats_are_private_to_each_user(auth_client: TestClient) -> None:
    auth_client.post("/analyze", json={"text": "Le chat mange.", "language": "fr"})
    auth_client.post("/auth/logout")
    other = {
        "name": "Alan Turing",
        "email": "alan@example.com",
        "password": "another-long-password",
    }
    auth_client.post("/auth/signup", json=other)

    body = auth_client.get("/stats", params={"period": "year"}).json()

    assert body["analyses"] == 0
    assert body["total_words"] == 0


def test_stats_reject_unknown_timezone(auth_client: TestClient) -> None:
    response = auth_client.get("/stats", params={"timezone": "Mars/Olympus"})

    assert response.status_code == 422


def test_month_bounds_roll_over_december() -> None:
    paris = ZoneInfo("Europe/Paris")

    start, end = period_bounds("month", paris, now=datetime(2026, 12, 15, 12, tzinfo=paris))

    assert (start.year, start.month, start.day) == (2026, 12, 1)
    assert (end.year, end.month, end.day) == (2027, 1, 1)


def test_day_bounds_follow_the_user_timezone() -> None:
    now = datetime(2026, 11, 4, 23, 30, tzinfo=UTC)  # already 5 November in Auckland

    start, _ = period_bounds("day", ZoneInfo("Pacific/Auckland"), now=now)

    assert start.day == 5


def test_elapsed_days_for_an_old_account_start_with_the_month() -> None:
    paris = ZoneInfo("Europe/Paris")
    now = datetime(2026, 11, 20, 12, tzinfo=paris)
    start, _ = period_bounds("month", paris, now=now)

    days = count_elapsed_days(start, datetime(2025, 1, 1, tzinfo=UTC), now, paris)

    assert days == 20


def test_elapsed_days_for_a_new_account_start_at_signup() -> None:
    paris = ZoneInfo("Europe/Paris")
    now = datetime(2026, 11, 20, 12, tzinfo=paris)
    start, _ = period_bounds("month", paris, now=now)

    days = count_elapsed_days(start, datetime(2026, 11, 18, 9, tzinfo=UTC), now, paris)

    assert days == 3


def test_words_per_day_for_a_brand_new_account(auth_client: TestClient) -> None:
    auth_client.post("/analyze", json={"text": "Le chat mange. Le chat dort.", "language": "fr"})

    body = auth_client.get("/stats", params={"period": "month"}).json()

    assert body["elapsed_days"] == 1
    assert body["words_per_day"] == 6.0
