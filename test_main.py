from datetime import date, timedelta

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_list_habit():
    r = client.post("/habits", json={"name": "Read 20 minutes"})
    assert r.status_code == 200
    hid = r.json()["id"]
    r2 = client.get("/habits")
    assert r2.status_code == 200
    assert any(h["id"] == hid for h in r2.json())


def test_checkin_flow():
    hid = client.post("/habits", json={"name": "Stretch"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 200
    r2 = client.get(f"/habits/{hid}/checkins")
    assert r2.json() == ["2026-09-22"]


def test_checkin_unknown_habit_404():
    r = client.post("/habits/99999/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 404


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def _new_habit(name: str = "Streak habit") -> int:
    return client.post("/habits", json={"name": name}).json()["id"]


def test_streak_no_checkins_is_zero():
    hid = _new_habit()
    r = client.get(f"/habits/{hid}/streak")
    assert r.status_code == 200
    assert r.json() == {"habit_id": hid, "streak": 0}


def test_streak_counts_consecutive_days_ending_today():
    hid = _new_habit()
    for n in (0, 1, 2):
        client.post(f"/habits/{hid}/checkin", json={"day": _days_ago(n)})
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 3


def test_streak_stops_at_gap():
    hid = _new_habit()
    for n in (0, 1, 3, 4):
        client.post(f"/habits/{hid}/checkin", json={"day": _days_ago(n)})
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 2


def test_streak_zero_when_today_missing():
    hid = _new_habit()
    for n in (1, 2):
        client.post(f"/habits/{hid}/checkin", json={"day": _days_ago(n)})
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 0


def test_streak_duplicate_checkins_count_once():
    hid = _new_habit()
    for n in (0, 0, 1):
        client.post(f"/habits/{hid}/checkin", json={"day": _days_ago(n)})
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 2


def test_streak_ignores_other_habits():
    hid = _new_habit()
    other = _new_habit("Other")
    client.post(f"/habits/{other}/checkin", json={"day": _days_ago(0)})
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 0


def test_streak_unknown_habit_404():
    r = client.get("/habits/99999/streak")
    assert r.status_code == 404
