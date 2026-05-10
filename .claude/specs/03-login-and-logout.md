# Spec: Login and Logout

## Overview
Implement session-based authentication for Spendly. The `/login` route gains a POST
handler that verifies a user's email and password against the database and writes their
identity into the Flask session. The `/logout` route clears that session and redirects
to the landing page. The navbar in `base.html` becomes auth-aware: logged-in users see
their name and a Logout link; guests see Sign in and Get started. This step establishes
the authentication foundation that all future protected routes will depend on.

## Depends on
- Step 01 — Database Setup (`users` table, `get_db()`)
- Step 02 — Registration (hashed passwords exist in the DB; `app.secret_key` set; flash
  block present in `base.html`)

## Routes
- `GET  /login`  — render login form — public
- `POST /login`  — verify credentials, start session, redirect to `/dashboard` — public
- `GET  /logout` — clear session, redirect to `/` — logged-in (graceful if called as guest)

## Database changes
No database changes. The existing `users` table has all required fields.

## Templates
- **Modify:** `templates/login.html`
  - Re-populate `email` field on failed login (never re-populate password)
  - Already renders `{{ error }}` via `auth-error` div — no structural change needed
- **Modify:** `templates/base.html`
  - Navbar becomes auth-aware: show user name + Logout when `session.user_id` is set,
    otherwise show Sign in + Get started

## Files to change
- `app.py` — add all auth imports (`sqlite3`, `request`, `redirect`, `url_for`, `flash`,
  `session`), `app.secret_key`, `check_password_hash` import; upgrade `/login` and
  `/logout` routes
- `templates/login.html` — re-populate email on error
- `templates/base.html` — conditional navbar links

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` is already in the venv.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting in SQL
- Verify passwords with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On login success store only `session['user_id']` (int) and `session['user_name']` (str)
- On login failure re-render `login.html` with an inline error and the submitted email
- Invalid email (no matching row) and wrong password must show the **same** generic error
  message — do not reveal which field was wrong
- Logout must call `session.clear()` then redirect to `url_for('landing')`
- `app.secret_key` must be set before any session or flash usage

## Definition of done
- [ ] `POST /login` with valid credentials creates a session and redirects to `/dashboard`
  (placeholder string response is acceptable until dashboard is built)
- [ ] `POST /login` with unknown email shows an inline error — no 500
- [ ] `POST /login` with wrong password shows the same generic error as unknown email
- [ ] The email field is re-populated after a failed login attempt
- [ ] `GET /logout` clears the session and redirects to the landing page
- [ ] Navbar shows "Hi, <name>" + Logout link when a user is logged in
- [ ] Navbar shows Sign in + Get started when no session exists
- [ ] Flash success message from registration ("Account created! Please sign in.") is
  visible on the login page after a redirect from `/register`
- [ ] `GET /login` still renders the empty form (no regression)
