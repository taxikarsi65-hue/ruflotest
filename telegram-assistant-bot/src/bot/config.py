"""Загрузка настроек бота из переменных окружения (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    allowed_user_id: int
    openai_api_key: str
    database_path: str


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    user_id_raw = os.getenv("ALLOWED_USER_ID", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    db_path = os.getenv("DATABASE_PATH", "data/bot.db").strip()

    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", token),
            ("ALLOWED_USER_ID", user_id_raw),
            ("OPENAI_API_KEY", openai_key),
        )
        if not value
    ]
    if missing:
        raise ConfigError(
            "В файле .env не заполнены обязательные переменные: "
            + ", ".join(missing)
            + ". Смотри docs/SETUP_GUIDE_RU.md."
        )

    try:
        allowed_user_id = int(user_id_raw)
    except ValueError as exc:
        raise ConfigError("ALLOWED_USER_ID в .env должен быть числом (твой Telegram ID).") from exc

    return Settings(
        telegram_token=token,
        allowed_user_id=allowed_user_id,
        openai_api_key=openai_key,
        database_path=db_path,
    )
