"""Кнопки бота: постоянное меню (аналог «горячих клавиш») и инлайн-меню."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.db import Database

IDEA_BTN = "💡 Идея"
CALORIES_BTN = "📸 Калории"
WEIGHT_BTN = "⚖️ Вес"
FINANCE_BTN = "💰 Финансы"
CALENDAR_BTN = "📅 Календарь"
REPORT_BTN = "📊 Отчёт"
CANCEL_BTN = "❌ Отмена"

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [IDEA_BTN, CALORIES_BTN],
        [WEIGHT_BTN, FINANCE_BTN],
        [CALENDAR_BTN, REPORT_BTN],
        [CANCEL_BTN],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


def finance_categories_keyboard(db: Database) -> InlineKeyboardMarkup:
    rows = []
    row: list[InlineKeyboardButton] = []
    for cat in db.list_categories():
        row.append(InlineKeyboardButton(cat["name"], callback_data=f"fin_cat:{cat['id']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("💵 Доход", callback_data="fin_income")])
    return InlineKeyboardMarkup(rows)


REPORT_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Этот месяц", callback_data="report:this")],
        [InlineKeyboardButton("Прошлый месяц", callback_data="report:prev")],
    ]
)

CALENDAR_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("➕ Добавить событие", callback_data="cal:add")],
        [
            InlineKeyboardButton("Сегодня", callback_data="cal:today"),
            InlineKeyboardButton("Неделя", callback_data="cal:week"),
        ],
    ]
)
