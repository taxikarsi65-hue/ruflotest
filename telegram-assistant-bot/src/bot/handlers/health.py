"""Здоровье: калории по фото еды + учёт веса."""
from __future__ import annotations

import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import Database
from bot.services.vision import estimate_calories
from bot.states import KEY_MODE, MODE_CALORIES, MODE_IDEA, MODE_WEIGHT


async def set_calories_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[KEY_MODE] = MODE_CALORIES
    await update.effective_message.reply_text("📸 Пришли фото еды — посчитаю калории.")


async def set_weight_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[KEY_MODE] = MODE_WEIGHT
    await update.effective_message.reply_text("⚖️ Напиши текущий вес в кг, например: 82.4")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Фото еды обрабатываем всегда, независимо от текущего режима — оно однозначно."""
    db: Database = context.bot_data["db"]
    openai_client = context.bot_data["openai"]
    user_id = update.effective_user.id

    photo = update.effective_message.photo[-1]  # самое большое разрешение
    tg_file = await photo.get_file()
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = Path(tmp_dir) / "food.jpg"
        await tg_file.download_to_drive(custom_path=str(local_path))
        await update.effective_message.reply_text("🔎 Смотрю на фото...")
        try:
            estimate = await estimate_calories(openai_client, local_path)
        except Exception as exc:
            await update.effective_message.reply_text(
                f"Не получилось определить калории: {exc}"
            )
            return

    db.add_food_log(
        user_id,
        description=estimate.description,
        calories=estimate.calories,
        protein_g=estimate.protein_g,
        fat_g=estimate.fat_g,
        carbs_g=estimate.carbs_g,
    )
    from datetime import date

    today_total = db.daily_calories(user_id, date.today())

    lines = [f"🍽 {estimate.description}"]
    if estimate.calories is not None:
        lines.append(f"≈ {estimate.calories} ккал")
    macros = []
    if estimate.protein_g is not None:
        macros.append(f"белки {estimate.protein_g} г")
    if estimate.fat_g is not None:
        macros.append(f"жиры {estimate.fat_g} г")
    if estimate.carbs_g is not None:
        macros.append(f"углеводы {estimate.carbs_g} г")
    if macros:
        lines.append(", ".join(macros))
    lines.append(f"\nВсего за сегодня: {today_total} ккал")
    context.user_data[KEY_MODE] = MODE_IDEA
    await update.effective_message.reply_text("\n".join(lines))


async def save_weight_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    normalized = text.strip().replace(",", ".")
    try:
        weight = float(normalized)
    except ValueError:
        await update.effective_message.reply_text(
            "Не понял вес. Пришли число, например: 82.4"
        )
        return

    previous = db.last_weight(user_id)
    db.add_weight_log(user_id, weight)
    context.user_data[KEY_MODE] = MODE_IDEA

    reply = f"⚖️ Записал вес: {weight} кг"
    if previous is not None:
        delta = weight - previous["weight_kg"]
        sign = "+" if delta >= 0 else ""
        reply += f" ({sign}{delta:.1f} кг с прошлого раза)"
    await update.effective_message.reply_text(reply)
