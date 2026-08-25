from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import MAIN_MENU, CANCEL_BTN
from bot.states import KEY_MODE, MODE_IDEA

WELCOME = (
    "Привет! Я твой личный помощник.\n\n"
    "💡 По умолчанию я жду голосовые или текстовые сообщения с идеями — "
    "просто наговори или напиши, ничего нажимать не нужно.\n\n"
    "Остальное — через кнопки внизу:\n"
    "📸 Калории — пришли фото еды, посчитаю калории\n"
    "⚖️ Вес — запишу твой вес\n"
    "💰 Финансы — запишу доход/расход по категориям\n"
    "📅 Календарь — запишу событие голосом или текстом и покажу список\n"
    "📊 Отчёт — сводка по финансам за месяц"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[KEY_MODE] = MODE_IDEA
    await update.effective_message.reply_text(WELCOME, reply_markup=MAIN_MENU)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[KEY_MODE] = MODE_IDEA
    await update.effective_message.reply_text(
        "Ок, вернулись в режим записи идей.", reply_markup=MAIN_MENU
    )


async def unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Этот бот приватный и настроен только на одного владельца."
    )
