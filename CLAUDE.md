# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (use a venv)
pip install -r requirements.txt

# Run the dev server (http://localhost:5001)
python app.py

# Run tests
pytest
```

## Architecture

**Single-file Flask app** — all routes live in `app.py`. There is no blueprint or application factory pattern. The app runs on port 5001.

**Template inheritance** — every page extends `templates/base.html`, which provides the navbar, footer, and loads `static/css/style.css` + `static/js/main.js` globally. Pages that need extra CSS or JS inject them via `{% block head %}` and `{% block scripts %}` respectively. `landing.css` is the only page-scoped stylesheet; it overrides `style.css` rules for the hero section by loading after it.

**CSS design system** — `style.css` defines all CSS custom properties at `:root`. Key tokens:
- `--ink` / `--ink-muted` / `--ink-soft` / `--ink-faint` — text hierarchy
- `--accent` (`#1a472a` forest green) / `--accent-light` — brand colour
- `--paper` / `--paper-card` — background surfaces
- `--border` / `--border-soft` — dividers
- `--font-display` (DM Serif Display) / `--font-body` (DM Sans)

When adding new UI, use these tokens rather than hardcoded colours.

**Database** — `database/db.py` is a scaffold stub (not yet implemented). The planned database is SQLite (`expense_tracker.db`, gitignored). The module exposes three functions to implement: `get_db()`, `init_db()`, `seed_db()`.

**Placeholder routes** — several routes in `app.py` return plain strings and are labelled with step numbers (Steps 3–9). These are intentional scaffolding for a guided curriculum; implement them in order as the curriculum progresses.

**No auth yet** — `login.html` and `register.html` have forms that POST to their routes, but the route handlers only handle GET (no POST branch, no session management, no password hashing).

**Tests** — `pytest` and `pytest-flask` are installed but no test files exist yet. Tests should live in a `tests/` directory at the project root.
