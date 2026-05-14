from database.db import get_db

VALID_CATEGORIES = ("Food", "Transport", "Bills", "Health",
                    "Entertainment", "Shopping", "Other")


def insert_expense(user_id, amount, category, date, description):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        db.commit()
    finally:
        db.close()
