"""Финансы: расходы по категориям, доходы, отчёт за месяц."""
from __future__ import annotations

import re
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import Database, MonthlyReport
from bot.keyboards import REPORT_KEYBOARD, finance_categories_keyboard
from bot.states import (
    KEY_FINANCE_CATEGORY_ID,
    KEY_FINANCE_KIND,
    KEY_MODE,
    MODE_FINANCE_AMOUNT,
    MODE_IDEA,
)

_AMOUNT_NOTE_RE = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*(.*)$")


def parse_amount_note(text: str) -> tuple[float, str | None] | None:
    """Достаёт сумму и необязательный комментарий из строки вида «1500 такси»."""
    match = _AMOUNT_NOTE_RE.match(text)
    if not match:
        return None
    amount = float(match.group(1).replace(",", "."))
    note = match.group(2).strip() or None
    return amount, note


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: Database = context.bot_data["db"]
    await update.effective_message.reply_text(
        "Выбери категорию расхода или запиши доход:",
        reply_markup=finance_categories_keyboard(db),
    )


async def on_category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split(":", 1)[1])
    db: Database = context.bot_data["db"]
    category = db.get_category(category_id)
    context.user_data[KEY_MODE] = MODE_FINANCE_AMOUNT
    context.user_data[KEY_FINANCE_CATEGORY_ID] = category_id
    context.user_data[KEY_FINANCE_KIND] = "expense"
    name = category["name"] if category else "категория"
    await query.edit_message_text(
        f"Категория: {name}\nНапиши сумму (можно с комментарием), например: 1500 такси"
    )


async def on_income_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data[KEY_MODE] = MODE_FINANCE_AMOUNT
    context.user_data[KEY_FINANCE_CATEGORY_ID] = None
    context.user_data[KEY_FINANCE_KIND] = "income"
    await query.edit_message_text("Доход. Напиши сумму, например: 3000 подработка")


async def save_finance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    parsed = parse_amount_note(text)
    if parsed is None:
        await update.effective_message.reply_text(
            "Не понял сумму. Напиши число первым, например: 1500 такси"
        )
        return

    amount, note = parsed
    kind = context.user_data.get(KEY_FINANCE_KIND, "expense")
    category_id = context.user_data.get(KEY_FINANCE_CATEGORY_ID)

    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    db.add_finance_entry(user_id, kind=kind, amount=amount, category_id=category_id, note=note)

    context.user_data[KEY_MODE] = MODE_IDEA
    label = "Доход" if kind == "income" else "Расход"
    await update.effective_message.reply_text(f"💰 {label} записан: {amount:g}" + (f" ({note})" if note else ""))


async def show_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("За какой период показать отчёт?", reply_markup=REPORT_KEYBOARD)


async def on_report_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id

    today = date.today()
    if query.data == "report:this":
        year, month = today.year, today.month
    else:
        year, month = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)

    report = db.monthly_report(user_id, year, month)
    await query.edit_message_text(_format_report(report))


def _format_report(report: MonthlyReport) -> str:
    lines = [f"📊 Отчёт за {report.month:02d}.{report.year}", ""]
    if report.by_category:
        for name, total in report.by_category:
            lines.append(f"  {name}: {total:g}")
    else:
        lines.append("  Расходов пока нет")
    lines.append("")
    lines.append(f"Доход: {report.income:g}")
    lines.append(f"Расход: {report.expense:g}")
    lines.append(f"Итого: {report.net:g}")
    return "\n".join(lines)
