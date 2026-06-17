# Dev Control Panel (`rplanner-dev`)

`rplanner-dev` is the local development CLI for Resource Planner. It provides an interactive menu-driven control panel and a non-interactive `--options` mode for scripted or CI use.

---

## Location

```
scripts/dev/
├── __init__.py
├── __main__.py          # Entry point (argparse + menu dispatch)
├── constants.py         # Shared path/colour constants
├── menu.py              # Interactive main_menu() and MENU_TREE
├── reset.py             # Setup reset script (called by Django Tools > Reset Setup)
│
├── core/
│   ├── cache.py         # File-hash-based skip cache for runserver pre-tasks
│   ├── env.py           # .env read/write helpers
│   ├── parallel.py      # Parallel column display and tab view for live processes
│   └── shell.py         # run(), _run_pytest(), pause() and non_interactive flag
│
└── modules/
    ├── autofix.py       # Ruff auto-fix
    ├── cleanup.py       # Cache directory removal
    ├── django_tools.py  # Migrations, server, reset, SQL runner
    ├── docker.py        # Docker Compose service management
    ├── keycloak.py      # Keycloak realm config and sync
    ├── precommit.py     # Pre-commit hook runner
    ├── sql.py           # Interactive SQL query runner
    ├── tests.py         # Django and package test runners
    └── tracker.py       # Test Tracker server launcher
```

---

## How to Run

### Interactive mode

```bash
python -m scripts.dev
```

Or, if installed via `pip install -e .`:

```bash
rplanner-dev
```

Launches the interactive menu. Use number keys to navigate, `0` to go back or exit.

### Non-interactive mode

```bash
python -m scripts.dev --options <N> [<N> ...]
rplanner-dev -o <N> [<N> ...]
```

Navigates the menu tree non-interactively using a sequence of option numbers. Interactive pauses (`press Enter to continue`) are suppressed automatically.

**Examples:**

```bash
# Cleanup > Python Cache
rplanner-dev -o 1 1

# Cleanup > Mypy Cache
rplanner-dev -o 1 2

# Django Tools > Make Migrations
rplanner-dev -o 3 1

# Django Tools > Migrate
rplanner-dev -o 3 2

# Run Tests > All
rplanner-dev -o 5 1

# Run Tests > Django > Unit
rplanner-dev -o 5 2 2
```

---

## Menu Reference

### Top-level menu

| Option | Label                  |
| ------ | ---------------------- |
| `1`    | Cleanup                |
| `2`    | Pre-Commit (all files) |
| `3`    | Django Tools           |
| `4`    | Install Requirements   |
| `5`    | Run Tests              |
| `6`    | Tools / Test Tracker   |
| `7`    | Docker                 |
| `8`    | Auto-Fix               |

---

### 1 — Cleanup

Removes tool-generated cache directories from the entire repository tree.

| Option | Label                          | Directory removed    |
| ------ | ------------------------------ | -------------------- |
| `1`    | Python Cache (`__pycache__`)   | All `__pycache__/`   |
| `2`    | Mypy Cache (`.mypy_cache`)     | All `.mypy_cache/`   |
| `3`    | Pytest Cache (`.pytest_cache`) | All `.pytest_cache/` |
| `4`    | Ruff Cache (`.ruff_cache`)     | All `.ruff_cache/`   |

Each action reports how many items were removed.

**Non-interactive example:**

```bash
rplanner-dev -o 1 3   # Clean .pytest_cache
```

---

### 2 — Pre-Commit (all files)

Runs the full pre-commit hook suite across all files in the repository:

```bash
pre-commit run --all-files
```

This executes ruff, mypy, bandit, prettier, and the CSS/JS builds exactly as they run during a `git commit`.

---

### 3 — Django Tools

Manages the Django application.

| Option | Label               | Description                                                         |
| ------ | ------------------- | ------------------------------------------------------------------- |
| `1`    | Make Migrations     | Discovers app labels from `settings.py` and runs `makemigrations`   |
| `2`    | Migrate             | Applies all pending migrations                                      |
| `3`    | Run Server          | Runs pre-build tasks then starts Django + Test Tracker side-by-side |
| `4`    | Reset Setup         | Wipes setup state; optionally a full clean including OAuth/SAML     |
| `5`    | SQL Query Runner    | Interactive REPL for running raw SQL against the configured DB      |
| `6`    | Keycloak Dev Config | Syncs Keycloak realm configuration for OAuth/SAML development       |

#### Run Server behaviour

Before starting `manage.py runserver`, the server option:

1. Checks file-hash caches to determine which pre-build tasks need to run
2. Runs changed tasks in parallel (PostCSS, esbuild, pip install, icon JSON generation)
3. Reads `.env` to detect which Docker services are configured
4. Starts any configured services (PostgreSQL, Mailpit, LocalStack, Keycloak) via Docker Compose
5. Launches Django (`0.0.0.0:8000`) and the Test Tracker (`port 8001`) in a side-by-side tab view
6. On `Ctrl+C`, terminates both processes, stops any Docker services it started, and cleans up written `.env` keys

---

### 4 — Install Requirements

Installs Python dependencies from `requirements/base.txt` and `requirements/dev.txt`:

```bash
pip install -r requirements/base.txt -r requirements/dev.txt
```

---

### 5 — Run Tests

Runs pytest across Django apps and/or standalone packages.

| Option | Label             | Description                                   |
| ------ | ----------------- | --------------------------------------------- |
| `1`    | All               | Runs Django and Packages suites, writes index |
| `2`    | Django (apps/web) | Sub-menu: All / Unit / Integration            |
| `3`    | Packages          | Sub-menu: All / Unit / Integration            |

#### Django sub-menu (`-o 5 2`)

| Option | Label       | pytest marker    | Distribution      |
| ------ | ----------- | ---------------- | ----------------- |
| `1`    | All         | none             | `--dist=loadfile` |
| `2`    | Unit        | `-m unit`        | `--dist=load`     |
| `3`    | Integration | `-m integration` | `--dist=loadfile` |

All Django runs use `-n auto --no-migrations` and write an HTML report to `.pytest-reports/`.

#### Packages sub-menu (`-o 5 3`)

| Option | Label       | pytest marker    |
| ------ | ----------- | ---------------- |
| `1`    | All         | none             |
| `2`    | Unit        | `-m unit`        |
| `3`    | Integration | `-m integration` |

Package runs use `-p no:django --import-mode=importlib` so all standalone packages can be collected in a single pytest call without Django.

#### Reports

HTML reports are written to `.pytest-reports/` at the repository root:

| File                               | Contents                            |
| ---------------------------------- | ----------------------------------- |
| `all-report.html`                  | Index linking to both suite reports |
| `django-report.html`               | Full Django test run                |
| `django-unit-report.html`          | Django unit tests only              |
| `django-integration-report.html`   | Django integration tests only       |
| `packages-report.html`             | All package tests                   |
| `packages-unit-report.html`        | Package unit tests only             |
| `packages-integration-report.html` | Package integration tests only      |

**Non-interactive examples:**

```bash
rplanner-dev -o 5 1       # All tests
rplanner-dev -o 5 2 2     # Django unit tests only
rplanner-dev -o 5 3 3     # Package integration tests only
```

---

### 6 — Tools / Test Tracker

Starts the local Test Tracker server on port `8001`:

```bash
python tools/test-tracker/server.py
```

Open `http://localhost:8001` in a browser. See [Test Tracker documentation](../architecture/test-tracker.md) for full details.

---

### 7 — Docker

Manages individual Docker Compose service profiles. Each action starts or restarts the named container using the configured `.env` settings.

| Option | Label            | Profile    | Container                         |
| ------ | ---------------- | ---------- | --------------------------------- |
| `1`    | PostgreSQL       | `postgres` | `resource-planner-dev-pg`         |
| `2`    | Email (Mailpit)  | `smtp`     | `resource-planner-dev-mailpit`    |
| `3`    | LocalStack       | `aws`      | `resource-planner-dev-localstack` |
| `4`    | Keycloak (OAuth) | `keycloak` | `resource-planner-dev-keycloak`   |
| `5`    | Keycloak (SAML)  | `keycloak` | `resource-planner-dev-keycloak`   |

Services are only started when the corresponding configuration is present in `.env`. If a service is not configured, the option prints a message and returns without starting anything.

---

### 8 — Auto-Fix

| Option | Label | Description                                 |
| ------ | ----- | ------------------------------------------- |
| `1`    | Ruff  | Runs `ruff check --fix` on all Python files |

---

## Package Structure

### `constants.py`

Defines shared path constants and ANSI colour helpers used throughout the package.

| Constant            | Value                                             |
| ------------------- | ------------------------------------------------- |
| `ROOT`              | Repository root (two levels above `scripts/dev/`) |
| `WEB_DIR`           | `apps/web`                                        |
| `PACKAGES_DIR`      | `packages/`                                       |
| `REPORTS_DIR`       | `.pytest-reports/`                                |
| `CACHE_DIR`         | `.dev-cache/`                                     |
| `TEST_TRACKER_DIR`  | `tools/test-tracker/`                             |
| `TEST_TRACKER_PORT` | `8001`                                            |

ANSI colours (`YELLOW`, `GREEN`, `RED`, `RESET`) are disabled automatically when stdout is not a TTY.

---

### `core/shell.py`

Provides the `run()` and `pause()` primitives used by all modules.

- `run(cmd, cwd=ROOT)` — runs a shell command, prints `>>> cmd`, returns the exit code
- `_run_pytest(cmd)` — like `run()` but treats exit code `5` (no tests collected) as success
- `pause()` — calls `input("Press Enter to continue...")` unless `non_interactive` is `True`
- `non_interactive` — module-level boolean; set to `True` by `__main__.py` when `--options` is passed

---

### `core/cache.py`

File-hash cache used by `runserver` to skip pre-build steps when their inputs have not changed.

- `_needs_run(name, paths)` — returns `True` if any path's mtime or content has changed since the last recorded run
- `_record_run(name, paths)` — writes the current hashes to `.dev-cache/<name>.json`

---

### `core/env.py`

Thin wrappers for reading and writing `apps/web/.env`.

- `_load_env_defaults()` — returns a dict of key/value pairs from `.env`
- `_env_write(key, value)` — appends or updates a key in `.env`
- `_env_remove(key)` — removes a key from `.env`
- `_prompt(label, default, secret)` — interactive prompt helper used by configuration flows

---

### `core/parallel.py`

Parallel execution and display utilities used by `runserver`.

- `_run_parallel_columns(tasks)` — runs multiple buffered tasks concurrently, displays output in side-by-side columns, returns `{name: returncode}`
- `_run_tab_view(tasks)` — runs long-lived processes (Django, Test Tracker) with a tab switcher UI that lets the developer view each process's live output

---

### `menu.py`

Defines `main_menu()` (the interactive loop) and `MENU_TREE` (the dict used for `--options` traversal).

`MENU_TREE` is a nested dict where each key is the option number as a string:

```python
MENU_TREE = {
    "1": {
        "label": "Cleanup",
        "action": cleanup_menu,        # called when -o 1 is the last option
        "children": {
            "1": {"label": "Python Cache", "action": clean_pycache},
            ...
        },
    },
    ...
}
```

`__main__.py` walks this tree with the list of `--options` values, calling `action()` on the final node.

---

## Installation

`rplanner-dev` is declared as a console script in `pyproject.toml`:

```toml
[project.scripts]
rplanner-dev = "scripts.dev.__main__:main"
```

Install in editable mode to make the command available in the activated virtualenv:

```bash
pip install -e .
```

After installation, both of the following are equivalent:

```bash
python -m scripts.dev --options 1 2
rplanner-dev -o 1 2
```
