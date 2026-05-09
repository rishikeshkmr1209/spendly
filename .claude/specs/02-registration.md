# Spec: Registration

## Overview
Implement the POST handler for `/register` so new users can create a Spendly account. The
`register.html` template and `users` table already exist; this step wires them together with
server-side validation, duplicate-email detection, password hashing, and a redirect to the
login page on success. On Sucess , the user is shown with a success mesage and redirected to the login page. No session is created here — authentication comes in the next step.

## Depends on
- Step 01 — Database Setup (users table must exist; `get_db()` must be working)

## Routes
- `POST /register` — receives name/email/password form data, validates, inserts user, redirects — public

The existing `GET /register` route in `app.py` - render registration form - public(already exists as stub, upgrade it)

## Database changes
No new tables or columns. The existing `users` table already has all required fields:
`id`, `name`, `email`, `password_hash`, `created_at`.

## Templates
- **Modify:** `templates/register.html`
  - Already renders `{{ error }}` — no structural changes needed
  - Optionally re-populate `value="{{ name }}"` and `value="{{ email }}"` on validation failure
    so the user does not have to retype their name and email

## Files to change
- `app.py` — add POST branch to the `/register` route; add `redirect`, `url_for`, `request`
  imports from Flask

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.generate_password_hash` is already imported in
`database/db.py` and available in the venv.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — never use string formatting in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before INSERT
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Catch the `sqlite3.IntegrityError` that fires on duplicate email; surface a friendly
  inline error via the existing `{{ error }}` block — do not let it bubble as a 500
- Validate server-side: name non-empty, valid email format (basic), password ≥ 8 chars,
  confirm password must match password
- On success redirect to `url_for('login')` — do NOT create a session in this step
- Re-render the form with the original `name` and `email` values on any error so the user
  does not lose their input

## Definition of done
- [ ] `POST /register` with valid data inserts a new row into `users` and redirects to `/login`
- [ ] Password stored in DB is a werkzeug hash, not plaintext
- [ ] Submitting a duplicate email shows an inline error message (no 500 error)
- [ ] Submitting a blank name shows an inline validation error
- [ ] Submitting a password shorter than 8 characters shows an inline validation error
- [ ] Submitting mismatched passwords shows an inline validation error
- [ ] After a validation error the name and email fields are re-populated (password fields stay blank)
- [ ] `GET /register` still renders the empty form (no regression)
- [ ] App starts without errors and `pytest` (if any tests exist) passes
