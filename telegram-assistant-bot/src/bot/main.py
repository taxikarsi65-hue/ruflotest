"""Точка входа: собирает бота и запускает polling."""
from __future__ import annotations

import logging

from openai import OpenAI
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import ConfigError, load_settings
from bot.db import Database
from bot.handlers import calendar, finance, health, ideas, router, start
from bot.keyboards import (
    CALENDAR_BTN,
    CALORIES_BTN,
    CANCEL_BTN,
    FINANCE_BTN,
    IDEA_BTN,
    REPORT_BTN,
    WEIGHT_BTN,
)

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO
)
logger = logging.getLogger("assistant-bot")


def build_application() -> Application:
    settings = load_settings()
    db = Database(settings.database_path)
    openai_client = OpenAI(api_key=settings.openai_api_key)

    application = Application.builder().token(settings.telegram_token).build()
    application.bot_data["db"] = db
    application.bot_data["openai"] = openai_client

    owner = filters.User(user_id=settings.allowed_user_id)
    unauthorized = ~owner

    application.add_handler(CommandHandler("start", start.start, filters=owner))
    application.add_handler(
        MessageHandler(unauthorized, start.unauthorized)
    )

    def btn(label: str) -> filters.Regex:
        return filters.Regex(f"^{label}$") & owner

    application.add_handler(MessageHandler(btn(CANCEL_BTN), start.cancel))
    application.add_handler(MessageHandler(btn(IDEA_BTN), ideas.set_idea_mode))
    application.add_handler(MessageHandler(btn(CALORIES_BTN), health.set_calories_mode))
    application.add_handler(MessageHandler(btn(WEIGHT_BTN), health.set_weight_mode))
    application.add_handler(MessageHandler(btn(FINANCE_BTN), finance.show_categories))
    application.add_handler(MessageHandler(btn(CALENDAR_BTN), calendar.show_menu))
    application.add_handler(MessageHandler(btn(REPORT_BTN), finance.show_report_menu))

    application.add_handler(
        CallbackQueryHandler(finance.on_category_chosen, pattern=r"^fin_cat:")
    )
    application.add_handler(
        CallbackQueryHandler(finance.on_income_chosen, pattern=r"^fin_income$")
    )
    application.add_handler(
        CallbackQueryHandler(finance.on_report_period, pattern=r"^report:")
    )
    application.add_handler(
        CallbackQueryHandler(calendar.on_calendar_action, pattern=r"^cal:")
    )

    application.add_handler(MessageHandler(filters.PHOTO & owner, health.on_photo))
    application.add_handler(MessageHandler(filters.VOICE & owner, router.on_voice))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & owner, router.on_text)
    )

    return application


def main() -> None:
    try:
        application = build_application()
    except ConfigError as exc:
        logger.error(str(exc))
        raise SystemExit(1) from exc

    logger.info("Бот запускается...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
