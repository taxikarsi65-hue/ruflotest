"""SQLite-хранилище бота. Один файл на диске, без внешней БД."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

DEFAULT_CATEGORIES = [
    "Еда",
    "Транспорт/Авто",
    "Жильё",
    "Спорт",
    "Здоровье",
    "Одежда",
    "Развлечения",
    "Прочее",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS food_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    calories INTEGER,
    protein_g REAL,
    fat_g REAL,
    carbs_g REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weight_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight_kg REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS finance_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER,
    kind TEXT NOT NULL CHECK (kind IN ('expense', 'income')),
    amount REAL NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES finance_categories(id)
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    event_time TEXT,
    source_text TEXT,
    created_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            self._seed_categories(conn)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _seed_categories(self, conn: sqlite3.Connection) -> None:
        for name in DEFAULT_CATEGORIES:
            conn.execute(
                "INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (name,)
            )

    # ---------- Идеи ----------

    def add_idea(self, user_id: int, text: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO ideas (user_id, text, created_at) VALUES (?, ?, ?)",
                (user_id, text, datetime.now().isoformat(timespec="seconds")),
            )
            return cur.lastrowid

    def list_ideas_on(self, user_id: int, day: date) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM ideas WHERE user_id = ? AND date(created_at) = ? "
                "ORDER BY created_at",
                (user_id, day.isoformat()),
            ).fetchall()

    def list_recent_ideas(self, user_id: int, limit: int = 10) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM ideas WHERE user_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()

    # ---------- Здоровье ----------

    def add_food_log(
        self,
        user_id: int,
        description: str,
        calories: Optional[int],
        protein_g: Optional[float] = None,
        fat_g: Optional[float] = None,
        carbs_g: Optional[float] = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO food_logs "
                "(user_id, description, calories, protein_g, fat_g, carbs_g, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    description,
                    calories,
                    protein_g,
                    fat_g,
                    carbs_g,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            return cur.lastrowid

    def add_weight_log(self, user_id: int, weight_kg: float) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO weight_logs (user_id, weight_kg, created_at) VALUES (?, ?, ?)",
                (user_id, weight_kg, datetime.now().isoformat(timespec="seconds")),
            )
            return cur.lastrowid

    def daily_calories(self, user_id: int, day: date) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(calories), 0) AS total FROM food_logs "
                "WHERE user_id = ? AND date(created_at) = ?",
                (user_id, day.isoformat()),
            ).fetchone()
            return int(row["total"])

    def last_weight(self, user_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM weight_logs WHERE user_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1",
                (user_id,),
            ).fetchone()

    # ---------- Финансы ----------

    def list_categories(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM finance_categories ORDER BY id").fetchall()

    def get_category(self, category_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM finance_categories WHERE id = ?", (category_id,)
            ).fetchone()

    def add_finance_entry(
        self,
        user_id: int,
        kind: str,
        amount: float,
        category_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> int:
        if kind not in ("expense", "income"):
            raise ValueError("kind must be 'expense' or 'income'")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO finance_entries "
                "(user_id, category_id, kind, amount, note, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    category_id,
                    kind,
                    amount,
                    note,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            return cur.lastrowid

    def monthly_report(self, user_id: int, year: int, month: int) -> "MonthlyReport":
        prefix = f"{year:04d}-{month:02d}"
        with self._connect() as conn:
            by_category = conn.execute(
                "SELECT fc.name AS name, SUM(fe.amount) AS total "
                "FROM finance_entries fe "
                "JOIN finance_categories fc ON fc.id = fe.category_id "
                "WHERE fe.user_id = ? AND fe.kind = 'expense' "
                "AND substr(fe.created_at, 1, 7) = ? "
                "GROUP BY fc.name ORDER BY total DESC",
                (user_id, prefix),
            ).fetchall()
            income_row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM finance_entries "
                "WHERE user_id = ? AND kind = 'income' AND substr(created_at, 1, 7) = ?",
                (user_id, prefix),
            ).fetchone()
            expense_row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM finance_entries "
                "WHERE user_id = ? AND kind = 'expense' AND substr(created_at, 1, 7) = ?",
                (user_id, prefix),
            ).fetchone()
        income = float(income_row["total"])
        expense = float(expense_row["total"])
        return MonthlyReport(
            year=year,
            month=month,
            income=income,
            expense=expense,
            net=income - expense,
            by_category=[(r["name"], float(r["total"])) for r in by_category],
        )

    # ---------- Календарь ----------

    def add_event(
        self,
        user_id: int,
        title: str,
        event_date: date,
        event_time: Optional[str] = None,
        source_text: Optional[str] = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO calendar_events "
                "(user_id, title, event_date, event_time, source_text, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    title,
                    event_date.isoformat(),
                    event_time,
                    source_text,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            return cur.lastrowid

    def list_events_between(
        self, user_id: int, start: date, end: date
    ) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM calendar_events WHERE user_id = ? "
                "AND event_date BETWEEN ? AND ? "
                "ORDER BY event_date, COALESCE(event_time, '99:99')",
                (user_id, start.isoformat(), end.isoformat()),
            ).fetchall()


@dataclass(frozen=True)
class MonthlyReport:
    year: int
    month: int
    income: float
    expense: float
    net: float
    by_category: list[tuple[str, float]]
