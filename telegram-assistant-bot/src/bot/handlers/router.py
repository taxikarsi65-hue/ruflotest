"""Диспетчер: обычные голосовые/текстовые сообщения направляются по текущему режиму."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers import calendar, finance, health, ideas
from bot.states import (
    KEY_MODE,
    MODE_CALENDAR,
    MODE_FINANCE_AMOUNT,
    MODE_IDEA,
    MODE_WEIGHT,
)


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mode = context.user_data.get(KEY_MODE, MODE_IDEA)
    if mode == MODE_CALENDAR:
        await calendar.save_calendar_voice(update, context)
    else:
        # Идея — режим по умолчанию для голосовых, это и есть «горячая клавиша»
        await ideas.save_idea_voice(update, context)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.text or ""
    mode = context.user_data.get(KEY_MODE, MODE_IDEA)

    if mode == MODE_WEIGHT:
        await health.save_weight_text(update, context, text)
    elif mode == MODE_FINANCE_AMOUNT:
        await finance.save_finance_amount(update, context, text)
    elif mode == MODE_CALENDAR:
        await calendar.save_calendar_text(update, context, text)
    else:
        await ideas.save_idea_text(update, context, text)
