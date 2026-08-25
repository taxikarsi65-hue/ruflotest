from datetime import datetime

from bot.services.dateparse import parse_event

NOW = datetime(2026, 8, 25, 10, 0)  # вторник


def test_tomorrow_with_time():
    result = parse_event("завтра встреча в 14:00 с Иваном", now=NOW)
    assert result.event_date == datetime(2026, 8, 26).date()
    assert result.event_time == "14:00"
    assert "Иван" in result.title


def test_today_without_explicit_date_falls_back():
    result = parse_event("гениальная идея про новый продукт", now=NOW)
    assert result.event_date == NOW.date()
    assert result.title == "гениальная идея про новый продукт"


def test_specific_weekday():
    result = parse_event("в пятницу созвон с командой в 10 утра", now=NOW)
    assert result.event_date.weekday() == 4  # пятница
    assert result.event_date >= NOW.date()


def test_next_week_date_only():
    result = parse_event("день рождения у мамы 15 сентября", now=NOW)
    assert result.event_date.month == 9
    assert result.event_date.day == 15


def test_numeric_date_dot_format():
    result = parse_event("15.09 сходить к врачу", now=NOW)
    assert (result.event_date.month, result.event_date.day) == (9, 15)


def test_day_after_tomorrow():
    result = parse_event("послезавтра сдать отчёт", now=NOW)
    assert result.event_date == datetime(2026, 8, 27).date()
    assert "сдать отчёт" in result.title


def test_no_date_defaults_to_today_and_keeps_full_text():
    result = parse_event("надо купить молоко", now=NOW)
    assert result.event_date == NOW.date()
    assert result.title == "надо купить молоко"
