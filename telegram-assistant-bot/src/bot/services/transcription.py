"""Распознавание голосовых сообщений через OpenAI Whisper."""
from __future__ import annotations

import asyncio
from pathlib import Path

from openai import OpenAI


def _transcribe_sync(client: OpenAI, audio_path: Path) -> str:
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru",
        )
    return transcript.text.strip()


async def transcribe_voice(client: OpenAI, audio_path: Path) -> str:
    """Отправляет аудиофайл в OpenAI и возвращает распознанный текст.

    python-telegram-bot скачивает голосовые как .ogg — Whisper API принимает
    этот формат напрямую, конвертация не нужна. Сетевой вызов блокирующий,
    поэтому выполняем его в отдельном потоке, чтобы не тормозить остального бота.
    """
    return await asyncio.to_thread(_transcribe_sync, client, audio_path)
