from bot.handlers.finance import parse_amount_note


def test_amount_with_note():
    assert parse_amount_note("1500 такси") == (1500.0, "такси")


def test_amount_with_decimal_comma():
    assert parse_amount_note("1500,50 обед") == (1500.5, "обед")


def test_amount_without_note():
    assert parse_amount_note("3000") == (3000.0, None)


def test_amount_invalid():
    assert parse_amount_note("такси 1500") is None
