"""Захват идей: голосом (через Whisper) или текстом. Это режим по умолчанию."""
from __future__ import annotations

import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import Database
from bot.services.transcription import transcribe_voice
from bot.states import KEY_MODE, MODE_IDEA


async def set_idea_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[KEY_MODE] = MODE_IDEA
    await update.effective_message.reply_text(
        "Записываю идеи. Просто наговори голосовое или напиши текст в любой момент."
    )


async def save_idea_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    text = text.strip()
    if not text:
        return
    db.add_idea(user_id, text)
    await update.effective_message.reply_text(f"💡 Идея записана:\n«{text}»")


async def save_idea_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await _transcribe_incoming_voice(update, context)
    if text is None:
        return
    await save_idea_text(update, context, text)


async def _transcribe_incoming_voice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str | None:
    voice = update.effective_message.voice
    if voice is None:
        return None
    openai_client = context.bot_data["openai"]
    tg_file = await voice.get_file()
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = Path(tmp_dir) / "voice.ogg"
        await tg_file.download_to_drive(custom_path=str(local_path))
        await update.effective_message.reply_text("🎙 Распознаю голос...")
        try:
            return await transcribe_voice(openai_client, local_path)
        except Exception as exc:  # сеть/квота OpenAI — не роняем бота
            await update.effective_message.reply_text(
                f"Не получилось распознать голос: {exc}"
            )
            return None
