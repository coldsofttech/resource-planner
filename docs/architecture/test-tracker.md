# Test Tracker

The Test Tracker is a lightweight, self-contained QA tool for manually executing, recording, and tracking the test cases for Resource Planner.

It runs as a standalone local web server — no Django, no external dependencies — and persists all results in a local SQLite database alongside the tool itself.

---

## Location

```
tools/test-tracker/
├── server.py          # Python HTTP server (stdlib only)
├── index.html         # Single-page frontend
├── static/
│   ├── app.js         # All frontend logic
│   └── app.css        # All styles
├── data/
│   ├── setup.json           # Setup > Setup Wizard
│   ├── login.json           # Auth > Login
│   ├── register.json        # Auth > Register
│   ├── forgot-password.json # Auth > Forgot Password
│   ├── oauth.json           # Auth > OAuth 2.0
│   └── saml.json            # Auth > SAML 2.0
└── tracker.db         # SQLite database (auto-created on first run)
```

---

## How to Run

Requires Python 3.x. No packages to install.

```bash
cd tools/test-tracker
python server.py
```

Open in a browser:

```
http://localhost:8001
```

The server also prints the local network IP so team members on the same network can access it during a test session.

Stop with `Ctrl+C`.

---

## How It Works

### Startup sequence

On launch, `server.py`:

1. Creates the SQLite database and schema if it does not exist (`init_db`)
2. Seeds test case definitions from every `data/*.json` file into the database (`seed_data`) — seeding is idempotent and skips modules that are already loaded
3. Starts a `ThreadingHTTPServer` on port `8001`

### Database schema

```
parent_modules     slug (PK), name, sort_order
modules            slug (PK), name, parent_slug (FK), sort_order, created_at
test_cases         id (PK), module_slug (FK), suite_id, suite_name,
                   scenario, steps, expected, severity, sort_order
test_results       id (PK, autoincrement), test_case_id (FK),
                   status (pass|fail|blocked|skip), notes, tested_at
custom_test_cases  id (PK, autoincrement), module_slug (FK),
                   custom_id, scenario, severity, status, notes,
                   is_reviewed, created_at
```

`parent_modules` defines the top-level groupings shown in the sidebar. Each `module` belongs to one `parent_module` via `parent_slug`. The sidebar renders parent groups in `sort_order` order, with sub-modules ordered within each group.

Results are append-only. The latest result per test case is always derived from `MAX(id)` grouped by `test_case_id`. This preserves full history while showing the most recent state at a glance.

Custom test cases store their run status directly in the record (not via a separate results table) since they are lightweight in-session observations.

---

## Test Case Definitions

Test cases are defined as JSON files in `data/`. Each file describes one sub-module.

### Format

```json
{
  "module": {
    "slug": "setup",
    "name": "Setup Wizard",
    "sort_order": 0,
    "parent": { "slug": "setup", "name": "Setup", "sort_order": 0 }
  },
  "suites": [
    {
      "id": "TC-S-100",
      "name": "Step 1: Admin Account",
      "test_cases": [
        {
          "id": "TC-S-101",
          "severity": "P0",
          "scenario": "Valid admin account advances to step 2",
          "steps": "Enter valid first name, last name, email, matching strong password. Click Next.",
          "expected": "Step 2 becomes active. No errors shown."
        }
      ]
    }
  ]
}
```

### Fields

| Field      | Required | Description                                                          |
| ---------- | -------- | -------------------------------------------------------------------- |
| `id`       | Yes      | Unique test case ID (e.g. `TC-S-101`)                                |
| `severity` | No       | `P0` Critical · `P1` High · `P2` Medium · `P3` Low. Defaults to `P2` |
| `scenario` | Yes      | One-line description of what is being tested                         |
| `steps`    | No       | Step-by-step instructions for the tester                             |
| `expected` | No       | The expected outcome after the steps are completed                   |

To add a new sub-module, create a new `.json` file in `data/` following the same structure. It will be loaded automatically on next server start.

### Parent module fields

| Field                      | Required | Description                                                   |
| -------------------------- | -------- | ------------------------------------------------------------- |
| `module.slug`              | Yes      | Unique identifier for the sub-module (e.g. `login`)           |
| `module.name`              | Yes      | Display name for the sub-module (e.g. `Login`)                |
| `module.sort_order`        | No       | Position within its parent group. Defaults to `0`.            |
| `module.parent.slug`       | No       | Slug of the parent group (e.g. `auth`). Creates it if new.    |
| `module.parent.name`       | No       | Display name of the parent group (e.g. `Auth`).               |
| `module.parent.sort_order` | No       | Position of the parent group in the sidebar. Defaults to `0`. |

Sub-module slugs must be unique across all files. Once a sub-module is seeded, changing its JSON file has no effect on the loaded data (seeding is skipped for existing slugs). To reload updated test cases, delete `tracker.db` and restart the server.

---

## UI Overview

### Header — Overall stats

The header bar shows aggregate pass/fail metrics across **all modules and all parent groups combined** — total cases, pass count, fail count, blocked count, and overall pass rate. This gives an at-a-glance view of the entire test run state regardless of which module is open.

### Sidebar — Module list

Lists all sub-modules grouped under their parent module. Each parent group is labelled with its name (e.g. **Setup**, **Auth**). Within each group, sub-modules are listed in defined order.

Each sub-module entry shows:

- Total test case count
- Pass / Fail / Blocked counts (if any results recorded)
- Pass rate percentage (once at least one case is run)

Click a sub-module to open it.

### Main area — Test Cases view

Displays all test cases for the active module, grouped by suite. Each suite is collapsible.

Each test case row shows:

| Column      | Description                                                           |
| ----------- | --------------------------------------------------------------------- |
| ID          | Unique case identifier. Click **history** to see all past results     |
| Scenario    | Description of the test. Click **steps & expected** to expand details |
| Sev         | Priority badge: P0 / P1 / P2 / P3                                     |
| Status      | Dropdown to record the result: Not Run / Pass / Fail / Blocked / Skip |
| Notes       | Free-text notes field saved alongside the result                      |
| Last Tested | Time since last result was recorded (hover for full timestamp)        |

### Recording a result

1. Set the **Status** dropdown for a test case
2. Optionally type a note in the **Notes** field
3. The result is saved automatically — no submit button

The row indicator (last column) shows a brief `✓` on save or `✗` on error.

Setting the status back to **Not Run** deletes the latest result and resets the case.

### Main area — Summary view

Switch using the **Summary** tab. Shows:

- Overall stat cards: Total / Pass / Fail / Blocked / Skip / Not Run
- Pass rate progress bar (colour-segmented by status)
- Per-suite breakdown table with pass rates

### Filtering

The filter bar above the test cases supports:

- **Search** — matches against scenario text or test case ID
- **Status filter** — show only cases with a specific status
- **Severity filter** — show only P0 / P1 / P2 / P3

All filters combine. The count indicator shows how many cases are currently visible. Use **Reset** to clear all filters.

### History drawer

Click **history** next to any test case ID to open the history drawer. Shows the last 20 recorded results for that case in reverse chronological order, including status, notes, and timestamp.

### Clear Results

The **Clear Results** button (top right of a module) deletes all recorded results for the entire module, returning every test case to Not Run. A confirmation dialog is shown before proceeding.

### Custom Test Cases

Testers can log new scenarios discovered during a test session without stopping.

Click **+ Add Test Case** (top right, next to Clear Results) to open the form:

| Field    | Required | Description                                                                                 |
| -------- | -------- | ------------------------------------------------------------------------------------------- |
| ID       | No       | Optional identifier (e.g. `TC-CUSTOM-01`). Leave blank if unknown — admin assigns one later |
| Scenario | Yes      | One-line description of the test scenario                                                   |
| Severity | No       | P0 / P1 / P2 / P3 — can be set by admin during review                                       |
| Status   | No       | Run status at the time of logging                                                           |
| Notes    | No       | Observations, steps, or context                                                             |

Custom test cases appear in a **Custom Test Cases** section below the original suites. Status and notes can be updated inline after creation.

#### Admin review workflow

Custom test cases start as **pending review**. The section header shows how many are pending (e.g. `⏳ 3 pending review`).

Admins can click **Mark Reviewed** on each custom row to acknowledge it. Reviewed rows are visually dimmed and the header updates to `✓ All reviewed` once all are processed.

To promote a custom test case into the official test suite:

1. Mark it as Reviewed in the tracker
2. Add it to the appropriate `data/<module>.json` file with a proper `id` and `severity`
3. Restart the server — it will appear as an official test case on next load

---

## API Reference

The server exposes a simple REST API used by the frontend.

| Method   | Path                                    | Description                               |
| -------- | --------------------------------------- | ----------------------------------------- |
| `GET`    | `/api/modules`                          | List all modules with stats               |
| `GET`    | `/api/modules/{slug}/test-cases`        | Test cases for a module, grouped by suite |
| `GET`    | `/api/modules/{slug}/summary`           | Module-level and suite-level stats        |
| `GET`    | `/api/modules/{slug}/custom-test-cases` | List custom test cases for a module       |
| `GET`    | `/api/test-cases/{id}/history`          | Last 20 results for a test case           |
| `POST`   | `/api/test-cases/{id}/result`           | Record a result `{ status, notes }`       |
| `POST`   | `/api/modules/{slug}/custom-test-cases` | Create a custom test case                 |
| `PATCH`  | `/api/custom-test-cases/{id}`           | Update a custom test case (partial)       |
| `DELETE` | `/api/test-cases/{id}/result`           | Clear all results for a test case         |
| `DELETE` | `/api/custom-test-cases/{id}`           | Delete a custom test case                 |
| `POST`   | `/api/modules/{slug}/clear`             | Clear all results for a module            |

Valid status values for original test cases: `pass`, `fail`, `blocked`, `skip`.

Valid status values for custom test cases: `""` (not run), `pass`, `fail`, `blocked`, `skip`.

---

## Severity Levels

| Level | Meaning                                                        |
| ----- | -------------------------------------------------------------- |
| P0    | Critical — system-breaking, blocks release                     |
| P1    | High — major feature impact, high priority to fix              |
| P2    | Medium — noticeable defect, fix before release where practical |
| P3    | Low — cosmetic or edge case, can be deferred                   |

---

## Adding a New Sub-Module

1. Create `tools/test-tracker/data/<sub-module-slug>.json`
2. Include a `"parent"` field in `"module"` with the parent group `slug`, `name`, and optional `sort_order`
3. Restart `server.py`
4. The sub-module appears in the sidebar under its parent group automatically

Sub-module slugs must be unique across all files. Once seeded, changes to a JSON file have no effect (seeding is skipped for existing slugs). To reload updated test cases, delete `tracker.db` and restart the server.

---

## Existing Modules

| Parent | Sub-module      | Slug              | Description                                                                                                            |
| ------ | --------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Setup  | Setup Wizard    | `setup`           | End-to-end tests for the 8-step setup wizard covering all configuration paths, validation, navigation, and submission  |
| Auth   | Login           | `login`           | Classic email/password login flow including error states, validation, security, and non-functional requirements        |
| Auth   | Register        | `register`        | Self-registration flow with validation, duplicate/disabled states, and security checks                                 |
| Auth   | Forgot Password | `forgot-password` | 3-step password reset flow: email request → OTP code entry → new password, including expiry and token reuse prevention |
| Auth   | OAuth 2.0       | `oauth`           | OAuth authorization flow, callback handling, state token validation, and provider configuration                        |
| Auth   | SAML 2.0        | `saml`            | SAML authorize/ACS flow, signature validation, attribute extraction, and provider configuration                        |
