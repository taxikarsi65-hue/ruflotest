"""Оценка калорийности еды по фотографии через OpenAI Vision."""
from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from openai import OpenAI

_PROMPT = (
    "Ты нутрициолог. На фото — еда. Оцени состав блюда и его примерную "
    "калорийность на всю порцию, видимую на фото. Отвечай СТРОГО в формате JSON "
    "без каких-либо пояснений вокруг, со следующими полями: "
    '{"description": "краткое название блюда по-русски", '
    '"calories": целое число ккал, '
    '"protein_g": число граммов белка, '
    '"fat_g": число граммов жира, '
    '"carbs_g": число граммов углеводов}. '
    "Если не уверен — дай разумную оценку, не отказывайся отвечать."
)


@dataclass(frozen=True)
class CalorieEstimate:
    description: str
    calories: Optional[int]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carbs_g: Optional[float]


def _estimate_sync(client: OpenAI, image_path: Path) -> CalorieEstimate:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    raw = response.choices[0].message.content or "{}"
    return parse_estimate(raw)


def parse_estimate(raw_json: str) -> CalorieEstimate:
    """Отдельная от сети функция — так парсинг ответа модели легко тестировать."""
    cleaned = raw_json.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    data = json.loads(cleaned)
    return CalorieEstimate(
        description=str(data.get("description", "блюдо")),
        calories=_to_int(data.get("calories")),
        protein_g=_to_float(data.get("protein_g")),
        fat_g=_to_float(data.get("fat_g")),
        carbs_g=_to_float(data.get("carbs_g")),
    )


def _to_int(value) -> Optional[int]:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _to_float(value) -> Optional[float]:
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


async def estimate_calories(client: OpenAI, image_path: Path) -> CalorieEstimate:
    return await asyncio.to_thread(_estimate_sync, client, image_path)
