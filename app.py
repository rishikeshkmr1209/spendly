import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            return render_template("register.html", error="Name is required.", name=name, email=email)
        if not email or "@" not in email:
            return render_template("register.html", error="Enter a valid email address.", name=name, email=email)
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.", name=name, email=email)

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with that email already exists.", name=name, email=email)
        finally:
            conn.close()

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.", email=email)

        session["user_id"]   = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    uid = session["user_id"]
    db = get_db()

    user = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?", (uid,)
    ).fetchone()

    stats = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS txn_count FROM expenses WHERE user_id = ?",
        (uid,)
    ).fetchone()

    top_cat_row = db.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (uid,)
    ).fetchone()

    recent = db.execute(
        "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10",
        (uid,)
    ).fetchall()

    by_category = db.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC",
        (uid,)
    ).fetchall()

    db.close()

    max_cat_total = max((r["cat_total"] for r in by_category), default=1)

    def fmt_date(d):
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y").lstrip("0")
        except ValueError:
            return d

    recent_fmt = [
        {"date": fmt_date(r["date"]), "description": r["description"],
         "category": r["category"], "amount": r["amount"]}
        for r in recent
    ]

    return render_template(
        "profile.html",
        user=user,
        total_spent=stats["total"],
        txn_count=stats["txn_count"],
        top_category=top_cat_row["category"] if top_cat_row else "—",
        recent=recent_fmt,
        by_category=by_category,
        max_cat_total=max_cat_total,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
