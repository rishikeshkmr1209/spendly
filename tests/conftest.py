import sqlite3
import pytest
import app as flask_app
import database.db as db_module
import database.queries as queries_module


@pytest.fixture
def test_app(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"

    def _get_test_db():
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(db_module, "get_db", _get_test_db)
    monkeypatch.setattr(queries_module, "get_db", _get_test_db)
    monkeypatch.setattr(flask_app, "get_db", _get_test_db)

    conn = _get_test_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret"
    with flask_app.app.test_client() as client:
        with flask_app.app.app_context():
            yield client, _get_test_db


@pytest.fixture
def logged_in_client(test_app):
    client, get_test_db = test_app
    from werkzeug.security import generate_password_hash
    conn = get_test_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@example.com", generate_password_hash("password123")),
    )
    conn.commit()
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Test User"

    return client, user_id, get_test_db
