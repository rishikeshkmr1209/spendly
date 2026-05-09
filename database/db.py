import sqlite3
import pathlib

from werkzeug.security import generate_password_hash

DB_PATH = pathlib.Path(__file__).parent.parent / "spendly.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] > 0:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    expenses = [
        (user_id, 450.0,  "Food",          "2026-05-02", "Groceries at Big Bazaar"),
        (user_id, 120.0,  "Transport",     "2026-05-03", "Uber to office"),
        (user_id, 1800.0, "Bills",         "2026-05-05", "Electricity bill"),
        (user_id, 350.0,  "Health",        "2026-05-07", "Pharmacy"),
        (user_id, 600.0,  "Entertainment", "2026-05-10", "Movie tickets"),
        (user_id, 2200.0, "Shopping",      "2026-05-12", "New shoes"),
        (user_id, 200.0,  "Other",         "2026-05-15", "Miscellaneous"),
        (user_id, 280.0,  "Food",          "2026-05-18", "Lunch at restaurant"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
