"""Прогон реальных обработчиков с поддельными Update/Context (без сети Telegram/OpenAI)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.db import Database
from bot.handlers import calendar, finance, router
from bot.states import KEY_FINANCE_CATEGORY_ID, KEY_FINANCE_KIND, KEY_MODE, MODE_FINANCE_AMOUNT


def make_update(text: str | None = None, user_id: int = 42):
    message = SimpleNamespace(text=text, reply_text=AsyncMock())
    return SimpleNamespace(effective_message=message, effective_user=SimpleNamespace(id=user_id))


def make_context(db: Database, user_data: dict | None = None):
    return SimpleNamespace(bot_data={"db": db}, user_data=user_data if user_data is not None else {})


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


@pytest.mark.asyncio
async def test_default_text_is_saved_as_idea(db):
    update = make_update("сделать классное приложение")
    context = make_context(db)

    await router.on_text(update, context)

    ideas = db.list_recent_ideas(42)
    assert len(ideas) == 1
    assert ideas[0]["text"] == "сделать классное приложение"
    update.effective_message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_finance_amount_flow_saves_entry_and_resets_mode(db):
    category = db.list_categories()[0]
    update = make_update("1500 такси")
    context = make_context(
        db,
        {
            KEY_MODE: MODE_FINANCE_AMOUNT,
            KEY_FINANCE_CATEGORY_ID: category["id"],
            KEY_FINANCE_KIND: "expense",
        },
    )

    await router.on_text(update, context)

    report = db.monthly_report(42, __import__("datetime").date.today().year, __import__("datetime").date.today().month)
    assert report.expense == 1500.0
    assert context.user_data[KEY_MODE] != MODE_FINANCE_AMOUNT


@pytest.mark.asyncio
async def test_calendar_view_shows_added_event(db):
    from datetime import date

    db.add_event(42, "Встреча с командой", date.today(), event_time="14:00")
    text = calendar._format_view(db, 42, date.today(), date.today())
    assert "Встреча с командой" in text
    assert "14:00" in text


@pytest.mark.asyncio
async def test_report_formatting_contains_totals(db):
    from datetime import date

    category = db.list_categories()[0]
    db.add_finance_entry(42, kind="expense", amount=1000, category_id=category["id"])
    db.add_finance_entry(42, kind="income", amount=5000)
    report = db.monthly_report(42, date.today().year, date.today().month)
    text = finance._format_report(report)
    assert "1000" in text
    assert "5000" in text
    assert "4000" in text  # net
