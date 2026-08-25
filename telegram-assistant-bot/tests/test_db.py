from datetime import date

import pytest

from bot.db import Database


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


def test_ideas_roundtrip(db):
    db.add_idea(1, "Сделать приложение")
    ideas = db.list_ideas_on(1, date.today())
    assert len(ideas) == 1
    assert ideas[0]["text"] == "Сделать приложение"


def test_food_and_daily_calories(db):
    db.add_food_log(1, "Салат", calories=300)
    db.add_food_log(1, "Суп", calories=250)
    db.add_food_log(2, "Чужой обед", calories=999)  # другой пользователь
    assert db.daily_calories(1, date.today()) == 550
    assert db.daily_calories(2, date.today()) == 999


def test_weight_log_and_last(db):
    assert db.last_weight(1) is None
    db.add_weight_log(1, 80.0)
    db.add_weight_log(1, 79.5)
    last = db.last_weight(1)
    assert last["weight_kg"] == 79.5


def test_finance_categories_seeded(db):
    categories = db.list_categories()
    names = {c["name"] for c in categories}
    assert len(categories) == 8
    assert "Еда" in names
    assert "Прочее" in names


def test_finance_monthly_report(db):
    categories = {c["name"]: c["id"] for c in db.list_categories()}
    today = date.today()

    db.add_finance_entry(1, kind="expense", amount=1000, category_id=categories["Еда"])
    db.add_finance_entry(1, kind="expense", amount=500, category_id=categories["Еда"])
    db.add_finance_entry(1, kind="expense", amount=2000, category_id=categories["Транспорт/Авто"])
    db.add_finance_entry(1, kind="income", amount=5000)

    report = db.monthly_report(1, today.year, today.month)
    assert report.income == 5000
    assert report.expense == 3500
    assert report.net == 1500
    by_cat = dict(report.by_category)
    assert by_cat["Еда"] == 1500
    assert by_cat["Транспорт/Авто"] == 2000


def test_finance_report_isolated_per_user(db):
    today = date.today()
    db.add_finance_entry(1, kind="income", amount=100)
    db.add_finance_entry(2, kind="income", amount=999)
    report = db.monthly_report(1, today.year, today.month)
    assert report.income == 100


def test_calendar_events_between(db):
    today = date.today()
    db.add_event(1, "Встреча", today, event_time="14:00")
    db.add_event(1, "Другой день", today.replace(day=1))
    events = db.list_events_between(1, today, today)
    assert len(events) == 1
    assert events[0]["title"] == "Встреча"
