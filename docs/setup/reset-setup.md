# Reset Setup

> **Warning:** This is a destructive operation. It deletes the admin user, user profile, and setup configuration. The application will re-enter the setup wizard on the next visit.

## When to use

- Re-running setup in a development or staging environment
- Recovering from a misconfigured initial setup
- Testing the setup wizard flow from scratch

## Prerequisites

- Python virtual environment activated
- Dependencies installed (`pip install -r requirements/base.txt`)
- Run from the repository root

## How to run

### Option 1 — Dev control panel (recommended)

```bash
python scripts/dev/dev.py
```

Select **Django Tools → Reset Setup** from the menu. You will be prompted to confirm before any data is deleted.

### Option 2 — Run the script directly

```bash
python scripts/dev/reset.py
```

You will be prompted to confirm before any data is deleted.

### After the reset

Restart the development server:

```bash
python apps/web/manage.py runserver
```

Navigate to `/` — you will be redirected to the setup wizard.

---

## What the script does

| Step | Action                                                                                     |
| ---- | ------------------------------------------------------------------------------------------ |
| 1    | Deletes `Configuration` rows for `SETUP_COMPLETE`, `APP_NAME`, `APP_URL`                   |
| 2    | Deletes `UserProfile` rows linked to superuser accounts                                    |
| 3    | Deletes all `User` rows where `is_superuser = True`                                        |
| 4    | Removes `DB_ENGINE`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` from `.env` |

> **Note:** Only superuser accounts created during setup are removed. Regular user accounts are not affected.

The script source lives at [`scripts/dev/reset.py`](../../scripts/dev/reset.py).
