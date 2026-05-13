import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path):
    """Point the db module at a fresh temp database for each test."""
    path = tmp_path / "test_spendly.db"
    original = db_module.DB_PATH
    db_module.DB_PATH = path
    db_module.init_db()
    yield path
    db_module.DB_PATH = original


@pytest.fixture
def user_id(db_path):
    """Insert a test user and return their id."""
    conn = db_module.get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("Test User", "test@spendly.com", generate_password_hash("password"), "2026-01-15 10:00:00"),
    )
    conn.commit()
    uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return uid


@pytest.fixture
def user_with_expenses(db_path, user_id):
    """Add seed expenses for the test user."""
    conn = db_module.get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 1800.0, "Bills",         "2026-05-05", "Electricity bill"),
            (user_id, 2200.0, "Shopping",      "2026-05-12", "New shoes"),
            (user_id, 450.0,  "Food",          "2026-05-02", "Groceries"),
            (user_id, 280.0,  "Food",          "2026-05-18", "Lunch"),
            (user_id, 120.0,  "Transport",     "2026-05-03", "Uber"),
        ],
    )
    conn.commit()
    conn.close()
    return user_id


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

def test_get_user_by_id_valid(db_path, user_id):
    result = get_user_by_id(user_id)
    assert result is not None
    assert result["name"] == "Test User"
    assert result["email"] == "test@spendly.com"
    assert result["member_since"] == "January 2026"


def test_get_user_by_id_nonexistent(db_path):
    assert get_user_by_id(99999) is None


# ---------------------------------------------------------------------------
# get_summary_stats
# ---------------------------------------------------------------------------

def test_get_summary_stats_with_expenses(db_path, user_with_expenses):
    stats = get_summary_stats(user_with_expenses)
    assert stats["total_spent"] == pytest.approx(4850.0)
    assert stats["transaction_count"] == 5
    assert stats["top_category"] == "Shopping"


def test_get_summary_stats_no_expenses(db_path, user_id):
    stats = get_summary_stats(user_id)
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


# ---------------------------------------------------------------------------
# get_recent_transactions
# ---------------------------------------------------------------------------

def test_get_recent_transactions_with_expenses(db_path, user_with_expenses):
    txns = get_recent_transactions(user_with_expenses)
    assert len(txns) == 5
    # Newest first — 2026-05-18 should be first
    assert "18" in txns[0]["date"]
    for t in txns:
        assert "date" in t
        assert "description" in t
        assert "category" in t
        assert "amount" in t


def test_get_recent_transactions_no_expenses(db_path, user_id):
    assert get_recent_transactions(user_id) == []


# ---------------------------------------------------------------------------
# get_category_breakdown
# ---------------------------------------------------------------------------

def test_get_category_breakdown_with_expenses(db_path, user_with_expenses):
    breakdown = get_category_breakdown(user_with_expenses)
    assert len(breakdown) == 4  # Bills, Shopping, Food, Transport

    # Ordered by amount descending
    amounts = [r["amount"] for r in breakdown]
    assert amounts == sorted(amounts, reverse=True)

    # pct values sum to exactly 100
    assert sum(r["pct"] for r in breakdown) == 100

    # Each entry has required keys
    for r in breakdown:
        assert "name" in r
        assert "amount" in r
        assert "pct" in r
        assert isinstance(r["pct"], int)


def test_get_category_breakdown_no_expenses(db_path, user_id):
    assert get_category_breakdown(user_id) == []


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.fixture
def app(db_path):
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_profile_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated(client, db_path, user_id):
    with client.session_transaction() as sess:
        sess["user_id"]   = user_id
        sess["user_name"] = "Test User"
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Test User" in response.data
    assert "&#8377;" in response.data.decode() or "₹" in response.data.decode()
