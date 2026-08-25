"""Режимы диалога, хранятся в context.user_data['mode'].

По умолчанию бот всегда в режиме MODE_IDEA — это и есть «горячая клавиша»:
достаточно просто наговорить голосовое сообщение в любой момент, без
дополнительных нажатий, и оно будет сохранено как идея.
"""

MODE_IDEA = "idea"
MODE_CALORIES = "calories"
MODE_WEIGHT = "weight"
MODE_FINANCE_AMOUNT = "finance_amount"
MODE_CALENDAR = "calendar"

KEY_MODE = "mode"
KEY_FINANCE_CATEGORY_ID = "finance_category_id"
KEY_FINANCE_KIND = "finance_kind"
