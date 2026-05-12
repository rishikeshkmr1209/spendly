---
name: flask-profile-dashboard
description: >
  Implements an authenticated profile or dashboard page in a Flask app that uses
  session-based auth, raw SQLite (no ORM), Jinja2 templates, and a CSS variable
  design system. Use this skill whenever the user asks to build a profile page,
  user dashboard, account page, or any route that should be login-protected and
  show logged-in user data. Also triggers for: "implement /profile", "show user
  details after login", "guard a route with session", "make the navbar show the
  user's name", "session-aware navbar", "display account info", or any similar
  task in a Flask/Jinja2/SQLite project.
---

# Flask Authenticated Profile Dashboard

## What this skill covers

A repeatable pattern for adding an authenticated spending dashboard to a Flask app:

1. **Auth-guarded route** — redirect unauthenticated visitors to login
2. **Multiple DB queries** — stat aggregates, recent rows, and grouped totals via raw SQLite
3. **Dashboard template** — stat cards + transactions table + category bar chart in Jinja2
4. **Session-aware navbar** — base template conditionally shows logged-in vs guest links
5. **Scoped CSS** — new component styles using the project's existing CSS variable tokens

This pattern works for any single-file or small-blueprint Flask app with:
- `session['user_id']` written on login
- A `users` table in SQLite with at least `name`, `email`, `created_at`
- An `expenses` table with `user_id`, `amount`, `category`, `date`, `description`
- A `base.html` that other templates extend
- A CSS design system built on `:root` custom properties

---

## Step 1 — Auth-guarded route with expense queries

Replace the `/profile` stub in `app.py`. Read the file first to locate the existing route.

```python
from datetime import datetime  # add to imports if not present

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
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS txn_count "
        "FROM expenses WHERE user_id = ?",
        (uid,)
    ).fetchone()

    top_cat_row = db.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (uid,)
    ).fetchone()

    recent = db.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC LIMIT 10",
        (uid,)
    ).fetchall()

    by_category = db.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC",
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
```

**Key rules:**
- Check `session.get("user_id")` first — redirect immediately if falsy
- Use `COALESCE(SUM(...), 0)` so a user with no expenses gets `0`, not `None`
- `max_cat_total` defaults to `1` (not `0`) to avoid division-by-zero in the template
- Format dates in Python; pass ready-to-render strings to the template
- Close `db` after all `.fetchall()` calls — it's a raw connection, not a context manager
- Never select or pass `password_hash` to the template

---

## Step 2 — Session-aware navbar in `base.html`

Find the navbar links section and wrap them in a session conditional:

```html
{% if session.get('user_id') %}
  <span class="nav-user">{{ session['user_name'] }}</span>
  <a href="{{ url_for('logout') }}" class="nav-link">Sign out</a>
{% else %}
  <a href="{{ url_for('login') }}">Sign in</a>
  <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
{% endif %}
```

- `session` is available in Jinja2 automatically — no need to pass it from the route
- Brand logo stays outside the conditional — always visible
- Use `Sign out` (not `Logout`) to match the Spendly design reference

---

## Step 3 — Dashboard template (`templates/profile.html`)

```html
{% extends "base.html" %}

{% block title %}Dashboard — Spendly{% endblock %}

{% block content %}
<section class="dashboard-section">
  <div class="dashboard-inner">

    <!-- Stat cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <span class="stat-label">Total Spent</span>
        <span class="stat-value">₹{{ "%.2f"|format(total_spent) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Transactions</span>
        <span class="stat-value">{{ txn_count }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Top Category</span>
        <span class="stat-value">{{ top_category }}</span>
      </div>
    </div>

    <!-- Main grid -->
    <div class="dashboard-grid">

      <!-- Recent Transactions -->
      <div class="dash-card">
        <h2 class="dash-card-title">Recent Transactions</h2>
        <table class="txn-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Category</th>
              <th class="txn-amount-col">Amount</th>
            </tr>
          </thead>
          <tbody>
            {% for t in recent %}
            <tr>
              <td class="txn-date">{{ t.date }}</td>
              <td class="txn-desc">{{ t.description }}</td>
              <td><span class="cat-badge cat-{{ t.category | lower }}">{{ t.category }}</span></td>
              <td class="txn-amount">₹{{ "%.2f"|format(t.amount) }}</td>
            </tr>
            {% else %}
            <tr><td colspan="4" class="txn-empty">No expenses yet.</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      <!-- By Category -->
      <div class="dash-card">
        <h2 class="dash-card-title">By Category</h2>
        <div class="cat-bars">
          {% for row in by_category %}
          {% set pct = (row.cat_total / max_cat_total * 100) | round(1) %}
          <div class="cat-bar-row">
            <div class="cat-bar-header">
              <span class="cat-bar-name">{{ row.category }}</span>
              <span class="cat-bar-amt">₹{{ "%.2f"|format(row.cat_total) }}</span>
            </div>
            <div class="cat-bar-track">
              <div class="cat-bar-fill cat-color-{{ row.category | lower }}" style="width: {{ pct }}%"></div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>

    </div>
  </div>
</section>
{% endblock %}
```

**Notes:**
- Bar width `pct` is computed in Jinja using `max_cat_total` passed from Python
- Category badge and bar fill classes are derived from `category | lower` — add a CSS rule per category name
- The `style="width: {{ pct }}%"` inline is the only place inline styles appear; it's necessary because the value is dynamic

---

## Step 4 — CSS (append to the project's main stylesheet)

Read the existing stylesheet first to confirm no `.dashboard-*` or `.stat-*` classes exist, and to check the `:root` token names in use.

```css
/* ── Navbar: logged-in state ── */
.nav-user {
  font-size: 0.9rem;
  color: var(--ink-muted);
}

.nav-link {
  font-size: 0.9rem;
  color: var(--ink-soft);
  text-decoration: none;
}

.nav-link:hover { color: var(--accent); }

/* ── Dashboard ── */
.dashboard-section {
  padding: 2.5rem 2rem 4rem;
}

.dashboard-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

/* Stat cards */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}

.stat-card {
  background: var(--paper-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.75rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-muted);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 2.25rem;
  color: var(--ink);
  line-height: 1.1;
}

/* Dashboard grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 1.25rem;
  align-items: start;
}

.dash-card {
  background: var(--paper-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.75rem 2rem;
}

.dash-card-title {
  font-family: var(--font-body);
  font-size: 1rem;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 1.5rem;
}

/* Transactions table */
.txn-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.txn-table thead th {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-faint);
  padding: 0 0 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--border-soft);
}

.txn-table thead th.txn-amount-col { text-align: right; }

.txn-table tbody tr { border-bottom: 1px solid var(--border-soft); }
.txn-table tbody tr:last-child { border-bottom: none; }

.txn-table tbody td {
  padding: 0.9rem 0;
  vertical-align: middle;
}

.txn-date {
  color: var(--ink-muted);
  white-space: nowrap;
  padding-right: 1rem !important;
}

.txn-desc { color: var(--ink); }

.txn-amount {
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
  white-space: nowrap;
}

.txn-empty {
  text-align: center;
  color: var(--ink-faint);
  padding: 2rem 0 !important;
}

/* Category badges */
.cat-badge {
  display: inline-block;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: 0.775rem;
  font-weight: 500;
  white-space: nowrap;
}

/* Add a rule per category — background + text colour only */
.cat-badge.cat-food          { background: #e8f5e9; color: #2e7d32; }
.cat-badge.cat-transport     { background: #fff3e0; color: #e65100; }
.cat-badge.cat-bills         { background: #e8eaf6; color: #3949ab; }
.cat-badge.cat-health        { background: #fce4ec; color: #c62828; }
.cat-badge.cat-entertainment { background: #f3e5f5; color: #6a1b9a; }
.cat-badge.cat-shopping      { background: #fff8e1; color: #f57f17; }
.cat-badge.cat-other         { background: var(--border-soft); color: var(--ink-muted); }

/* Category bars */
.cat-bars { display: flex; flex-direction: column; gap: 1.1rem; }
.cat-bar-row { display: flex; flex-direction: column; gap: 0.35rem; }

.cat-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.875rem;
}

.cat-bar-name { color: var(--ink-soft); font-weight: 500; }

.cat-bar-amt {
  color: var(--ink-muted);
  font-variant-numeric: tabular-nums;
  font-size: 0.825rem;
}

.cat-bar-track {
  height: 5px;
  background: var(--border-soft);
  border-radius: 999px;
  overflow: hidden;
}

.cat-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s ease;
}

/* One fill colour per category */
.cat-color-shopping      { background: #c17f24; }
.cat-color-other         { background: #9e9e9e; }
.cat-color-food          { background: #2e7d32; }
.cat-color-bills         { background: #3949ab; }
.cat-color-health        { background: #c62828; }
.cat-color-entertainment { background: #6a1b9a; }
.cat-color-transport     { background: #e65100; }

/* Dashboard responsive */
@media (max-width: 900px) {
  .stat-cards { grid-template-columns: 1fr 1fr; }
  .dashboard-grid { grid-template-columns: 1fr; }
}

@media (max-width: 600px) {
  .stat-cards { grid-template-columns: 1fr; }
  .dashboard-section { padding: 1.5rem 1rem 3rem; }
}
```

**Note on hardcoded hex in badge/bar colours:** badge background/text and bar fill colours are intentionally explicit here because they encode category-specific meaning (green = food, red = health, etc.) and there are no matching semantic tokens in the design system. These are the only hex values permitted outside `:root`.

---

## Verification checklist

- [ ] `GET /profile` while logged in → renders dashboard with stat cards, table, and category bars
- [ ] Stat cards show correct ₹ total, transaction count, and top category name
- [ ] Transactions table shows last 10 expenses with category badges and formatted amounts
- [ ] By Category bars are proportional — highest category fills 100%, others scale accordingly
- [ ] `GET /profile` while logged out → redirects to `/login` (no 500, no flash of content)
- [ ] Navbar shows username + "Sign out" when session is active
- [ ] Navbar shows Sign in + Get started when no session
- [ ] Sign out clears session and redirects to landing page
- [ ] `password_hash` is never selected or passed to a template
- [ ] All SQL queries use `?` placeholders

## Common pitfalls

| Mistake | Fix |
|---|---|
| `SUM` returning `None` when no rows | Wrap with `COALESCE(SUM(amount), 0)` |
| Division by zero in bar widths | Default `max_cat_total` to `1`, not `0` |
| Forgetting `db.close()` | Call after all `.fetchall()` — it's a raw connection |
| Date formatting in Jinja | Do `strftime` in the route; pass formatted strings |
| String-formatting SQL | Always `?`, never f-string or `.format()` |
| Wrong session key name | Read the login route first to confirm the exact key written |
| Missing category CSS rule | Add both a `.cat-badge.cat-<name>` and `.cat-color-<name>` rule for each new category |
