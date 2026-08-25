import pytest

from bot.services.vision import parse_estimate


def test_parse_plain_json():
    raw = '{"description": "Гречка с курицей", "calories": 450, "protein_g": 35, "fat_g": 10, "carbs_g": 50}'
    est = parse_estimate(raw)
    assert est.description == "Гречка с курицей"
    assert est.calories == 450
    assert est.protein_g == 35.0


def test_parse_json_in_markdown_fence():
    raw = "```json\n{\"description\": \"Салат\", \"calories\": 200}\n```"
    est = parse_estimate(raw)
    assert est.description == "Салат"
    assert est.calories == 200
    assert est.protein_g is None


def test_parse_missing_fields_are_none():
    raw = '{"description": "Что-то"}'
    est = parse_estimate(raw)
    assert est.calories is None
    assert est.fat_g is None
