from datetime import datetime

from database.db import get_db


def _date_clause(date_from, date_to):
    if date_from and date_to:
        return " AND date BETWEEN ? AND ?", (date_from, date_to)
    return "", ()


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    try:
        member_since = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except ValueError:
        member_since = row["created_at"]
    return {"name": row["name"], "email": row["email"], "member_since": member_since}


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    clause, date_params = _date_clause(date_from, date_to)
    stats = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count"
        f" FROM expenses WHERE user_id = ?{clause}",
        (user_id,) + date_params,
    ).fetchone()
    top = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ?"
        f"{clause} GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,) + date_params,
    ).fetchone()
    conn.close()
    return {
        "total_spent": stats["total_spent"],
        "transaction_count": stats["transaction_count"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    clause, date_params = _date_clause(date_from, date_to)
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses"
        f" WHERE user_id = ?{clause} ORDER BY date DESC LIMIT ?",
        (user_id,) + date_params + (limit,),
    ).fetchall()
    conn.close()

    def fmt_date(d):
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y").lstrip("0")
        except ValueError:
            return d

    return [
        {
            "date": fmt_date(r["date"]),
            "description": r["description"],
            "category": r["category"],
            "amount": r["amount"],
        }
        for r in rows
    ]


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    clause, date_params = _date_clause(date_from, date_to)
    rows = conn.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses"
        f" WHERE user_id = ?{clause} GROUP BY category ORDER BY cat_total DESC",
        (user_id,) + date_params,
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(r["cat_total"] for r in rows)
    result = [
        {"name": r["category"], "amount": r["cat_total"], "pct": int(r["cat_total"] / grand_total * 100)}
        for r in rows
    ]

    # Adjust largest category so pct values sum exactly to 100
    remainder = 100 - sum(item["pct"] for item in result)
    result[0]["pct"] += remainder

    return result
