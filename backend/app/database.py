from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "leaders.csv"


SAMPLE_LEADERS = [
    {
        "name": "Jacinda Ardern",
        "country": "New Zealand",
        "photo_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Emmanuel Macron",
        "country": "France",
        "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Sanna Marin",
        "country": "Finland",
        "photo_url": "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Volodymyr Zelenskyy",
        "country": "Ukraine",
        "photo_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tsai Ing-wen",
        "country": "Taiwan",
        "photo_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Justin Trudeau",
        "country": "Canada",
        "photo_url": "https://images.unsplash.com/photo-1506795660185-b5b3b1c1fdf9?auto=format&fit=crop&w=900&q=80",
    },
]


def load_environment() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def get_database_url() -> str:
    load_environment()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env before starting the API.")
    return database_url


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_database_url(), row_factory=dict_row)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leaders (
                id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                photo_url TEXT NOT NULL,
                elo INTEGER NOT NULL DEFAULT 1400,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                winner_id INTEGER NOT NULL,
                loser_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (winner_id) REFERENCES leaders(id),
                FOREIGN KEY (loser_id) REFERENCES leaders(id)
            )
            """
        )
        sync_leaders_from_csv(connection)
        seed_leaders_if_empty(connection)
        connection.commit()


def seed_leaders_if_empty(connection: psycopg.Connection) -> None:
    existing_count = connection.execute("SELECT COUNT(*) AS count FROM leaders").fetchone()["count"]
    if existing_count > 0:
        return

    leaders = load_leaders_from_csv()
    if not leaders:
        leaders = SAMPLE_LEADERS

    insert_leaders(connection, leaders)


def sync_leaders_from_csv(connection: psycopg.Connection) -> None:
    leaders = load_leaders_from_csv()
    if not leaders:
        return

    existing_count = connection.execute("SELECT COUNT(*) AS count FROM leaders").fetchone()["count"]
    if existing_count == len(leaders):
        existing_rows = connection.execute(
            "SELECT name, country, photo_url FROM leaders ORDER BY name, country, photo_url"
        ).fetchall()
        existing_leaders = [dict(row) for row in existing_rows]
        incoming_leaders = sorted(leaders, key=lambda leader: (leader["name"], leader["country"], leader["photo_url"]))
        if existing_leaders == incoming_leaders:
            return

    connection.execute("TRUNCATE TABLE votes, leaders RESTART IDENTITY")
    insert_leaders(connection, leaders)


def load_leaders_from_csv() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        return []

    with CSV_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        leaders = []
        for row in reader:
            name = first_present_value(row, "name", "headLabel")
            country = first_present_value(row, "country", "countryLabel")
            photo_url = first_present_value(row, "photo_url", "image")
            if name and country and photo_url:
                leaders.append(
                    {
                        "name": name,
                        "country": country,
                        "photo_url": photo_url,
                    }
                )
        return leaders


def insert_leaders(connection: psycopg.Connection, leaders: list[dict[str, str]]) -> None:
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO leaders (name, country, photo_url, elo, wins, losses)
            VALUES (%(name)s, %(country)s, %(photo_url)s, 1400, 0, 0)
            """,
            leaders,
        )


def first_present_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return value
    return ""
