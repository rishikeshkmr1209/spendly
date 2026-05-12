# Spec: Profile Page (Dashboard)

## Overview
Build the authenticated dashboard page for Spendly. After login, users are redirected to
`/profile`, which displays a spending summary dashboard — stat cards at the top, a recent
transactions table, and a by-category breakdown — all fetched live from the `expenses` and
`users` tables. The route enforces authentication: unauthenticated visitors are redirected
to `/login`. The navbar in `base.html` is updated to be session-aware, showing the user's
name and a "Sign out" link for logged-in users instead of Sign in / Get started.

## Depends on
- Step 01 — Database Setup (`users` + `expenses` tables, `get_db()`)
- Step 03 — Login and Logout (session keys `user_id` and `user_name` written on login)

## Routes
- `GET /profile` — render dashboard with spending stats and transactions — logged-in only
  (redirect to `/login` if no session)

## Database changes
No schema changes. Queries against the existing `users` and `expenses` tables.

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - **Stat cards row** (3 cards): Total Spent, Transactions count, Top Category
  - **Dashboard grid** (2 columns):
    - Left (~60%): Recent Transactions table — date, description, category badge, amount
    - Right (~40%): By Category — horizontal bar per category, sized relative to the highest
  - Category badges and bar fill colours are keyed by lowercase category name
- **Modify:** `templates/base.html`
  - Navbar becomes session-aware:
    - Logged-in: show username (non-link) + "Sign out" link (`url_for('logout')`)
    - Guest: show existing "Sign in" + "Get started" links

## Files to change
- `app.py` — replace placeholder `/profile` route with a handler that:
  - Checks `session.get('user_id')` — if missing, redirect to `url_for('login')`
  - Runs **4 queries** for the logged-in user:
    1. `SUM(amount)` + `COUNT(*)` for total spent and transaction count
    2. Top category by `SUM(amount) DESC LIMIT 1`
    3. Last 10 expenses ordered by `date DESC`
    4. All categories grouped by total, ordered `DESC` (for bar chart)
  - Computes `max_cat_total` in Python for bar width percentages
  - Formats each expense date (`%Y-%m-%d` → `"DD Mon YYYY"`) in Python
  - Passes all computed values to `profile.html`
- `templates/base.html` — session-aware navbar (username + "Sign out" vs guest links)
- `static/css/style.css` — append dashboard component styles (see CSS section below)

## Files to create
- `templates/profile.html` — dashboard page

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting in SQL
- Passwords: do not SELECT or display `password_hash`
- Use CSS variables — never hardcode hex values in new CSS
- All templates extend `base.html`
- Authentication check: if `session.get('user_id')` is falsy, `redirect(url_for('login'))`
- Format dates and compute bar percentages in the route — keep Jinja templates logic-free
- Bar widths: `pct = (cat_total / max_cat_total * 100)` — pass `max_cat_total` from Python

## Definition of done
- [ ] `GET /profile` while logged in renders the dashboard with stat cards, table, and bars
- [ ] Stat cards show correct Total Spent (₹), Transactions count, and Top Category name
- [ ] Transactions table shows date, description, category badge, and amount for last 10 expenses
- [ ] By Category panel shows a bar per category, widths proportional to spend
- [ ] `GET /profile` while not logged in redirects to `/login` — no 500, no visible page
- [ ] Navbar shows username + "Sign out" link when a user is logged in
- [ ] Navbar shows Sign in + Get started when no session is active
- [ ] Sign out link works: clears session and redirects to landing page
- [ ] Dashboard uses only CSS variable tokens — no hardcoded hex values
- [ ] `password_hash` is never passed to or rendered in the template
- [ ] All SQL queries use `?` placeholders
