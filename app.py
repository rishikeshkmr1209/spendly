import sqlite3
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

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


def _parse_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except (ValueError, TypeError):
        return None


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    uid = session["user_id"]

    # --- Preset date ranges ---
    today = date.today()

    this_month_from = today.replace(day=1).isoformat()
    this_month_to   = today.isoformat()

    m3 = today.month - 3
    y3 = today.year + (m3 - 1) // 12
    m3 = ((m3 - 1) % 12) + 1
    last3_from = date(y3, m3, today.day).isoformat()

    m6 = today.month - 6
    y6 = today.year + (m6 - 1) // 12
    m6 = ((m6 - 1) % 12) + 1
    last6_from = date(y6, m6, today.day).isoformat()

    presets = [
        {"label": "This Month",    "date_from": this_month_from, "date_to": this_month_to},
        {"label": "Last 3 Months", "date_from": last3_from,      "date_to": today.isoformat()},
        {"label": "Last 6 Months", "date_from": last6_from,      "date_to": today.isoformat()},
        {"label": "All Time",      "date_from": None,             "date_to": None},
    ]

    # --- Parse & validate query params ---
    raw_from  = request.args.get("date_from", "").strip() or None
    raw_to    = request.args.get("date_to",   "").strip() or None
    date_from = _parse_date(raw_from)
    date_to   = _parse_date(raw_to)

    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.", "error")
        date_from = date_to = None

    # --- Active preset detection ---
    active_preset = None
    for p in presets:
        if p["date_from"] == date_from and p["date_to"] == date_to:
            active_preset = p["label"]
            break

    user      = get_user_by_id(uid)
    stats     = get_summary_stats(uid, date_from=date_from, date_to=date_to)
    recent    = get_recent_transactions(uid, date_from=date_from, date_to=date_to)
    breakdown = get_category_breakdown(uid, date_from=date_from, date_to=date_to)

    by_category   = [{"category": r["name"], "cat_total": r["amount"]} for r in breakdown]
    max_cat_total = max((r["cat_total"] for r in by_category), default=1)

    return render_template(
        "profile.html",
        user=user,
        total_spent=stats["total_spent"],
        txn_count=stats["transaction_count"],
        top_category=stats["top_category"],
        recent=recent,
        by_category=by_category,
        max_cat_total=max_cat_total,
        presets=presets,
        active_preset=active_preset,
        date_from=date_from or "",
        date_to=date_to or "",
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
