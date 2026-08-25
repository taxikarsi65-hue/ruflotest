"""Разбор русской фразы вида «завтра встреча в 14:00 с Иваном» на дату/время/название.

Реализовано вручную (регулярки + словари), а не через dateparser.search:
на практике та библиотека в русской локали иногда «теряет» число дня рядом
со словом «день» или разносит дату и время на два несвязанных совпадения
(«завтра» отдельно, «в 14:00» отдельно, без склейки). Здесь логика проще,
но предсказуема и покрыта тестами на реальных фразах.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

_MONTHS = {
    "январ": 1, "феврал": 2, "март": 3, "апрел": 4, "ма": 5, "июн": 6,
    "июл": 7, "август": 8, "сентябр": 9, "октябр": 10, "ноябр": 11, "декабр": 12,
}
_MONTH_RE = "|".join(sorted(_MONTHS, key=len, reverse=True))

_WEEKDAYS = {
    "понедельник": 0, "вторник": 1, "сред": 2, "четверг": 3,
    "пятниц": 4, "суббот": 5, "воскресен": 6,
}
_WEEKDAY_RE = "|".join(sorted(_WEEKDAYS, key=len, reverse=True))

_DAYPART_OFFSET = {"утра": 0, "ночи": 0, "дня": 12, "вечера": 12}

_DATE_PATTERNS = [
    # 15 сентября / 15 сентября 2026
    re.compile(
        rf"\b(?P<day>\d{{1,2}})\s+(?P<month>{_MONTH_RE})\w*(?:\s+(?P<year>\d{{4}}))?\b",
        re.IGNORECASE,
    ),
    # 15.09 / 15.09.2026 / 15/09/2026
    re.compile(r"\b(?P<day>\d{1,2})[./](?P<month>\d{1,2})(?:[./](?P<year>\d{4}))?\b"),
]

_RELATIVE_RE = re.compile(r"\b(послезавтра|завтра|сегодня)\b", re.IGNORECASE)
_WEEKDAY_PATTERN_RE = re.compile(
    rf"\bво?\s*(?P<wd>{_WEEKDAY_RE})\w*\b", re.IGNORECASE
)

_TIME_COLON_RE = re.compile(r"\b(?P<h>[01]?\d|2[0-3]):(?P<m>[0-5]\d)\b")
_TIME_WORD_RE = re.compile(
    r"\bв?\s*(?P<h>\d{1,2})\s*(?:час(?:а|ов)?)?\s*(?P<part>утра|дня|вечера|ночи)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedEvent:
    title: str
    event_date: date
    event_time: Optional[str]  # "HH:MM" или None, если время не найдено


def parse_event(text: str, *, now: Optional[datetime] = None) -> ParsedEvent:
    """Находит в тексте дату и время, остаток текста делает названием события.

    Если дата не найдена вовсе — событие ставится на сегодня, а весь текст
    становится названием (лучше сохранить с сегодняшней датой, чем потерять запись).
    """
    now = now or datetime.now()
    remaining = text

    event_date, remaining = _extract_date(remaining, now)
    event_time, remaining = _extract_time(remaining)

    title = _clean_title(remaining) or text.strip()
    return ParsedEvent(title=title, event_date=event_date, event_time=event_time)


def _extract_date(text: str, now: datetime) -> tuple[date, str]:
    match = _RELATIVE_RE.search(text)
    if match:
        word = match.group(1).lower()
        offset = {"сегодня": 0, "завтра": 1, "послезавтра": 2}[word]
        return now.date() + timedelta(days=offset), _cut(text, match)

    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        day = int(match.group("day"))
        month_raw = match.group("month")
        month = _MONTHS[month_raw.lower()] if not month_raw.isdigit() else int(month_raw)
        year = int(match.group("year")) if match.group("year") else now.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if not match.group("year") and candidate < now.date():
            candidate = date(year + 1, month, day)
        return candidate, _cut(text, match)

    match = _WEEKDAY_PATTERN_RE.search(text)
    if match:
        target = _WEEKDAYS[match.group("wd").lower()]
        offset = (target - now.weekday()) % 7
        return now.date() + timedelta(days=offset), _cut(text, match)

    return now.date(), text


def _extract_time(text: str) -> tuple[Optional[str], str]:
    match = _TIME_COLON_RE.search(text)
    if match:
        return f"{int(match.group('h')):02d}:{match.group('m')}", _cut(text, match)

    match = _TIME_WORD_RE.search(text)
    if match:
        hour = int(match.group("h")) % 12
        hour += _DAYPART_OFFSET[match.group("part").lower()]
        return f"{hour:02d}:00", _cut(text, match)

    return None, text


def _cut(text: str, match: re.Match) -> str:
    return (text[: match.start()] + " " + text[match.end():]).strip()


def _clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip(" ,.-—:")
    for filler in ("встреча", "напоминание", "событие"):
        if title.lower() == filler:
            return ""
    return title
