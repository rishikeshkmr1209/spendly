import pytest
from database.queries import insert_expense


VALID_POST = {
    "amount": "50.0",
    "category": "Food",
    "date": "2026-03-20",
    "description": "Lunch",
}


class TestInsertExpense:
    def test_inserts_row_with_description(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        insert_expense(
            user_id=user_id,
            amount=50.0,
            category="Food",
            date="2026-03-20",
            description="Lunch",
        )
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND category = 'Food'",
            (user_id,),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["amount"] == 50.0
        assert row["category"] == "Food"
        assert row["date"] == "2026-03-20"
        assert row["description"] == "Lunch"

    def test_inserts_row_with_null_description(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        insert_expense(
            user_id=user_id,
            amount=25.0,
            category="Transport",
            date="2026-03-21",
            description=None,
        )
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND category = 'Transport'",
            (user_id,),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["description"] is None


class TestGetAddExpense:
    def test_unauthenticated_get_redirects_to_login(self, test_app):
        client, _ = test_app
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_get_returns_200(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.get("/expenses/add")
        assert response.status_code == 200

    def test_authenticated_get_contains_form(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.get("/expenses/add")
        body = response.data.decode()
        assert "<form" in body
        assert "POST" in body

    def test_authenticated_get_contains_all_7_categories(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.get("/expenses/add")
        body = response.data.decode()
        for cat in ("Food", "Transport", "Bills", "Health",
                    "Entertainment", "Shopping", "Other"):
            assert cat in body


class TestPostAddExpense:
    def test_unauthenticated_post_redirects_to_login(self, test_app):
        client, _ = test_app
        response = client.post("/expenses/add", data=VALID_POST)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_valid_post_redirects_to_profile(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data=VALID_POST)
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_valid_post_inserts_row(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        client.post("/expenses/add", data=VALID_POST)
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["amount"] == 50.0
        assert row["category"] == "Food"

    def test_missing_amount_rerenders_with_error(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data={**VALID_POST, "amount": ""})
        assert response.status_code == 200
        assert b"Amount" in response.data

    def test_zero_amount_rerenders_with_error(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data={**VALID_POST, "amount": "0"})
        assert response.status_code == 200

    def test_non_numeric_amount_rerenders_with_error(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data={**VALID_POST, "amount": "abc"})
        assert response.status_code == 200

    def test_invalid_category_rerenders_with_error(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data={**VALID_POST, "category": "Gambling"})
        assert response.status_code == 200

    def test_invalid_date_rerenders_with_error(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data={**VALID_POST, "date": "not-a-date"})
        assert response.status_code == 200

    def test_missing_description_succeeds_with_null(self, logged_in_client):
        client, user_id, get_db = logged_in_client
        response = client.post("/expenses/add", data={**VALID_POST, "description": ""})
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]
        conn = get_db()
        row = conn.execute(
            "SELECT description FROM expenses WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
        assert row["description"] is None
