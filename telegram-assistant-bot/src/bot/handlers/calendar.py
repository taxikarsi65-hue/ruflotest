"""Календарь: запись событий голосом/текстом с автоматическим разбором даты/времени."""
from __future__ import annotations

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import Database
from bot.keyboards import CALENDAR_KEYBOARD
from bot.services.dateparse import parse_event
from bot.services.transcription import transcribe_voice
from bot.states import KEY_MODE, MODE_CALENDAR, MODE_IDEA


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Календарь: что сделать?", reply_markup=CALENDAR_KEYBOARD
    )


async def on_calendar_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]

    if action == "add":
        context.user_data[KEY_MODE] = MODE_CALENDAR
        await query.edit_message_text(
            "Скажи или напиши событие, например: «завтра встреча в 14:00 с Иваном»"
        )
        return

    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    today = date.today()
    if action == "today":
        start = end = today
    else:  # week
        start, end = today, today + timedelta(days=7)

    await query.edit_message_text(_format_view(db, user_id, start, end))


async def save_calendar_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    text = text.strip()
    if not text:
        return
    parsed = parse_event(text)
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    db.add_event(
        user_id,
        title=parsed.title,
        event_date=parsed.event_date,
        event_time=parsed.event_time,
        source_text=text,
    )
    context.user_data[KEY_MODE] = MODE_IDEA

    when = parsed.event_date.strftime("%d.%m.%Y")
    if parsed.event_time:
        when += f" в {parsed.event_time}"
    await update.effective_message.reply_text(f"📅 Записал: «{parsed.title}»\n{when}")


async def save_calendar_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice = update.effective_message.voice
    if voice is None:
        return
    openai_client = context.bot_data["openai"]
    tg_file = await voice.get_file()
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = Path(tmp_dir) / "voice.ogg"
        await tg_file.download_to_drive(custom_path=str(local_path))
        await update.effective_message.reply_text("🎙 Распознаю голос...")
        try:
            text = await transcribe_voice(openai_client, local_path)
        except Exception as exc:
            await update.effective_message.reply_text(f"Не получилось распознать голос: {exc}")
            return
    await save_calendar_text(update, context, text)


def _format_view(db: Database, user_id: int, start: date, end: date) -> str:
    events = db.list_events_between(user_id, start, end)
    by_day: dict[str, list[str]] = {}
    for ev in events:
        entry = f"  • {ev['title']}"
        if ev["event_time"]:
            entry += f" в {ev['event_time']}"
        by_day.setdefault(ev["event_date"], []).append(entry)

    day = start
    lines = ["📅 Календарь:"]
    while day <= end:
        iso = day.isoformat()
        label = day.strftime("%d.%m (%a)")
        if iso == date.today().isoformat():
            label += " — сегодня"
        lines.append(f"\n{label}")
        day_lines = by_day.get(iso)
        if day_lines:
            lines.extend(day_lines)
        else:
            lines.append("  (пусто)")
        day += timedelta(days=1)
    return "\n".join(lines)
