#!/usr/bin/env python3
"""
Resource Planner — Test Tracker
Run:  python server.py
Open: http://localhost:8001
"""

import json
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "tracker.db"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
PORT = 8001

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css",
    ".js": "application/javascript",
    ".ico": "image/x-icon",
}
VALID_STATUSES = {"pass", "fail", "blocked", "skip"}
VALID_CUSTOM_STATUSES = {"", "pass", "fail", "blocked", "skip"}


# ── Database ──────────────────────────────────────────────────────────────────


def _add_column_if_missing(
    c: sqlite3.Connection, table: str, column: str, typedef: str
) -> None:
    cols = {row[1] for row in c.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {typedef}")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_db() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS parent_modules (
                slug       TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS modules (
                slug       TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS test_cases (
                id          TEXT PRIMARY KEY,
                module_slug TEXT NOT NULL REFERENCES modules(slug),
                suite_id    TEXT NOT NULL,
                suite_name  TEXT NOT NULL,
                scenario    TEXT NOT NULL,
                steps       TEXT DEFAULT '',
                expected    TEXT DEFAULT '',
                severity    TEXT DEFAULT 'P2',
                sort_order  INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS test_results (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id TEXT NOT NULL REFERENCES test_cases(id),
                status       TEXT NOT NULL
                             CHECK(status IN ('pass','fail','blocked','skip')),
                notes        TEXT DEFAULT '',
                tested_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS custom_test_cases (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                module_slug  TEXT NOT NULL REFERENCES modules(slug),
                custom_id    TEXT DEFAULT '',
                scenario     TEXT NOT NULL,
                severity     TEXT DEFAULT '',
                status       TEXT DEFAULT '',
                notes        TEXT DEFAULT '',
                is_reviewed  INTEGER DEFAULT 0,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_res_tc  ON test_results(test_case_id);
            CREATE INDEX IF NOT EXISTS idx_res_ts  ON test_results(tested_at DESC);
            CREATE INDEX IF NOT EXISTS idx_cust_mod ON custom_test_cases(module_slug);
        """)
    # Safe column migrations for existing databases
    with get_db() as c:
        _add_column_if_missing(c, "modules", "parent_slug", "TEXT")
        _add_column_if_missing(c, "modules", "sort_order", "INTEGER DEFAULT 0")


def seed_data() -> None:
    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        mod = data["module"]
        slug = mod["slug"]
        parent = mod.get("parent")
        sort_order = mod.get("sort_order", 0)

        with get_db() as c:
            if parent:
                c.execute(
                    (
                        "INSERT OR IGNORE INTO parent_modules(slug,name,sort_order) "
                        "VALUES(?,?,?)"
                    ),
                    (parent["slug"], parent["name"], parent.get("sort_order", 0)),
                )

            c.execute(
                (
                    "INSERT OR IGNORE INTO modules(slug,name,parent_slug,sort_order) "
                    "VALUES(?,?,?,?)"
                ),
                (slug, mod["name"], parent["slug"] if parent else None, sort_order),
            )
            # Migrate existing rows that predate the parent concept
            if parent:
                c.execute(
                    (
                        "UPDATE modules SET parent_slug=?, sort_order=? WHERE slug=? "
                        "AND parent_slug IS NULL"
                    ),
                    (parent["slug"], sort_order, slug),
                )

            order = 0
            for suite in data["suites"]:
                for tc in suite["test_cases"]:
                    c.execute(
                        "INSERT OR IGNORE INTO test_cases"
                        "(id,module_slug,suite_id,suite_name,scenario,steps,expected,severity,sort_order)"
                        " VALUES(?,?,?,?,?,?,?,?,?)",
                        (
                            tc["id"],
                            slug,
                            suite["id"],
                            suite["name"],
                            tc["scenario"],
                            tc.get("steps", ""),
                            tc.get("expected", ""),
                            tc.get("severity", "P2"),
                            order,
                        ),
                    )
                    order += 1


# ── Query helpers ─────────────────────────────────────────────────────────────

_LATEST = """
    SELECT test_case_id, status, notes, tested_at
    FROM   test_results
    WHERE  id IN (
        SELECT MAX(id) FROM test_results GROUP BY test_case_id
    )
"""


def _stats(c: sqlite3.Connection, where: str, *params):
    return c.execute(
        f"""
        SELECT
            COUNT(*)                                                      AS total,
            COALESCE(SUM(CASE WHEN r.status='pass'    THEN 1 END), 0)    AS pass,
            COALESCE(SUM(CASE WHEN r.status='fail'    THEN 1 END), 0)    AS fail,
            COALESCE(SUM(CASE WHEN r.status='blocked' THEN 1 END), 0)    AS blocked,
            COALESCE(SUM(CASE WHEN r.status='skip'    THEN 1 END), 0)    AS skip,
            MAX(r.tested_at)                                              AS last_tested
        FROM  test_cases tc
        LEFT JOIN ({_LATEST}) r ON tc.id = r.test_case_id
        {where}
    """,
        params,
    ).fetchone()


# ── API logic ─────────────────────────────────────────────────────────────────


def api_modules():
    with get_db() as c:
        out = []
        for m in c.execute("""
            SELECT m.slug, m.name, m.parent_slug,
                   pm.name                       AS parent_name,
                   COALESCE(pm.sort_order, 999)  AS parent_sort_order
            FROM   modules m
            LEFT JOIN parent_modules pm ON m.parent_slug = pm.slug
            ORDER  BY COALESCE(pm.sort_order, 999),
                      COALESCE(m.sort_order, 0),
                      m.name
        """):
            s = _stats(c, "WHERE tc.module_slug=?", m["slug"])
            not_run = s["total"] - s["pass"] - s["fail"] - s["blocked"] - s["skip"]
            out.append(
                {
                    "slug": m["slug"],
                    "name": m["name"],
                    "parent_slug": m["parent_slug"],
                    "parent_name": m["parent_name"],
                    "parent_sort_order": m["parent_sort_order"],
                    "stats": {
                        "total": s["total"],
                        "pass": s["pass"],
                        "fail": s["fail"],
                        "blocked": s["blocked"],
                        "skip": s["skip"],
                        "not_run": not_run,
                        "last_tested": s["last_tested"],
                    },
                }
            )
        return out


def api_test_cases(slug: str):
    with get_db() as c:
        rows = c.execute(
            f"""
            SELECT tc.id, tc.suite_id, tc.suite_name, tc.scenario,
                   tc.steps, tc.expected, tc.severity, tc.sort_order,
                   r.status, r.notes, r.tested_at
            FROM   test_cases tc
            LEFT JOIN ({_LATEST}) r ON tc.id = r.test_case_id
            WHERE  tc.module_slug = ?
            ORDER  BY tc.sort_order
        """,
            (slug,),
        ).fetchall()

        suites, index = [], {}
        for row in rows:
            sid = row["suite_id"]
            if sid not in index:
                entry = {"id": sid, "name": row["suite_name"], "cases": []}
                index[sid] = entry
                suites.append(entry)
            index[sid]["cases"].append(
                {
                    "id": row["id"],
                    "scenario": row["scenario"],
                    "steps": row["steps"],
                    "expected": row["expected"],
                    "severity": row["severity"],
                    "status": row["status"],
                    "notes": row["notes"] or "",
                    "tested_at": row["tested_at"],
                }
            )
        return suites


def api_summary(slug: str):
    with get_db() as c:
        m = c.execute("SELECT slug, name FROM modules WHERE slug=?", (slug,)).fetchone()
        if not m:
            return None

        ov = _stats(c, "WHERE tc.module_slug=?", slug)
        not_run = ov["total"] - ov["pass"] - ov["fail"] - ov["blocked"] - ov["skip"]

        suites = []
        for row in c.execute(
            "SELECT DISTINCT suite_id, suite_name FROM test_cases"
            " WHERE module_slug=? ORDER BY sort_order",
            (slug,),
        ):
            s = _stats(
                c, "WHERE tc.module_slug=? AND tc.suite_id=?", slug, row["suite_id"]
            )
            nr = s["total"] - s["pass"] - s["fail"] - s["blocked"] - s["skip"]
            suites.append(
                {
                    "id": row["suite_id"],
                    "name": row["suite_name"],
                    "total": s["total"],
                    "pass": s["pass"],
                    "fail": s["fail"],
                    "blocked": s["blocked"],
                    "skip": s["skip"],
                    "not_run": nr,
                }
            )

        return {
            "module": dict(m),
            "overall": {
                "total": ov["total"],
                "pass": ov["pass"],
                "fail": ov["fail"],
                "blocked": ov["blocked"],
                "skip": ov["skip"],
                "not_run": not_run,
                "last_tested": ov["last_tested"],
            },
            "suites": suites,
        }


def api_save_result(tc_id: str, status: str, notes: str):
    if status not in VALID_STATUSES:
        return None, "invalid_status"
    with get_db() as c:
        if not c.execute("SELECT 1 FROM test_cases WHERE id=?", (tc_id,)).fetchone():
            return None, "not_found"
        c.execute(
            "INSERT INTO test_results(test_case_id,status,notes) VALUES(?,?,?)",
            (tc_id, status, notes),
        )
        row = c.execute(
            "SELECT * FROM test_results WHERE id=last_insert_rowid()"
        ).fetchone()
        return dict(row), None


def api_history(tc_id: str):
    with get_db() as c:
        if not c.execute("SELECT 1 FROM test_cases WHERE id=?", (tc_id,)).fetchone():
            return None
        rows = c.execute(
            "SELECT id, status, notes, tested_at FROM test_results"
            " WHERE test_case_id=? ORDER BY id DESC LIMIT 20",
            (tc_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def api_clear_case(tc_id: str):
    """Delete all results for a single test case, resetting it to Not Run."""
    with get_db() as c:
        if not c.execute("SELECT 1 FROM test_cases WHERE id=?", (tc_id,)).fetchone():
            return False, "not_found"
        c.execute("DELETE FROM test_results WHERE test_case_id=?", (tc_id,))
        return True, None


def api_clear_module(slug: str):
    """Delete all results for every test case in a module."""
    with get_db() as c:
        if not c.execute("SELECT 1 FROM modules WHERE slug=?", (slug,)).fetchone():
            return False, "not_found"
        c.execute(
            "DELETE FROM test_results WHERE test_case_id IN "
            "(SELECT id FROM test_cases WHERE module_slug=?)",
            (slug,),
        )
        return True, None


# ── Custom test case helpers ──────────────────────────────────────────────────

_CUSTOM_FIELDS = (
    "id, custom_id, scenario, severity, status, notes, is_reviewed, created_at"
)


def api_list_custom_cases(slug: str):
    with get_db() as c:
        if not c.execute("SELECT 1 FROM modules WHERE slug=?", (slug,)).fetchone():
            return None
        rows = c.execute(
            (
                f"SELECT {_CUSTOM_FIELDS} FROM custom_test_cases "
                "WHERE module_slug=? ORDER BY id"
            ),
            (slug,),
        ).fetchall()
        return [dict(r) for r in rows]


def api_create_custom_case(slug: str, data: dict):
    scenario = (data.get("scenario") or "").strip()
    if not scenario:
        return None, "scenario_required"
    status = (data.get("status") or "").strip()
    if status not in VALID_CUSTOM_STATUSES:
        return None, "invalid_status"
    with get_db() as c:
        if not c.execute("SELECT 1 FROM modules WHERE slug=?", (slug,)).fetchone():
            return None, "not_found"
        c.execute(
            (
                "INSERT INTO custom_test_cases(module_slug,custom_id,scenario,severity,"
                "status,notes) VALUES(?,?,?,?,?,?)"
            ),
            (
                slug,
                (data.get("custom_id") or "").strip(),
                scenario,
                (data.get("severity") or "").strip(),
                status,
                (data.get("notes") or "").strip(),
            ),
        )
        row = c.execute(
            (
                f"SELECT {_CUSTOM_FIELDS} FROM custom_test_cases WHERE "
                "id=last_insert_rowid()"
            )
        ).fetchone()
        return dict(row), None


def api_update_custom_case(case_id: int, data: dict):
    with get_db() as c:
        if not c.execute(
            "SELECT 1 FROM custom_test_cases WHERE id=?", (case_id,)
        ).fetchone():
            return None, "not_found"
        fields, params = [], []
        if "scenario" in data:
            scenario = (data["scenario"] or "").strip()
            if not scenario:
                return None, "scenario_required"
            fields.append("scenario=?")
            params.append(scenario)
        if "custom_id" in data:
            fields.append("custom_id=?")
            params.append((data["custom_id"] or "").strip())
        if "severity" in data:
            fields.append("severity=?")
            params.append((data["severity"] or "").strip())
        if "status" in data:
            status = (data["status"] or "").strip()
            if status not in VALID_CUSTOM_STATUSES:
                return None, "invalid_status"
            fields.append("status=?")
            params.append(status)
        if "notes" in data:
            fields.append("notes=?")
            params.append((data["notes"] or "").strip())
        if "is_reviewed" in data:
            fields.append("is_reviewed=?")
            params.append(1 if data["is_reviewed"] else 0)
        if fields:
            params.append(case_id)
            c.execute(
                f"UPDATE custom_test_cases SET {', '.join(fields)} WHERE id=?", params
            )
        row = c.execute(
            f"SELECT {_CUSTOM_FIELDS} FROM custom_test_cases WHERE id=?", (case_id,)
        ).fetchone()
        return dict(row), None


def api_delete_custom_case(case_id: int):
    with get_db() as c:
        if not c.execute(
            "SELECT 1 FROM custom_test_cases WHERE id=?", (case_id,)
        ).fetchone():
            return False, "not_found"
        c.execute("DELETE FROM custom_test_cases WHERE id=?", (case_id,))
        return True, None


# ── HTTP handler ──────────────────────────────────────────────────────────────


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: D401
        print(f"  {self.address_string()}  {fmt % args}")

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(json.dumps(data).encode(), "application/json", status)

    def _file(self, path: Path) -> None:
        if not path.exists():
            self._json({"error": "not_found"}, 404)
            return
        ct = MIME.get(path.suffix, "text/plain")
        self._send(path.read_bytes(), ct)

    def _read_body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_GET(self) -> None:  # noqa: N802
        try:
            p = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"

            if p in ("/", "/index.html"):
                return self._file(BASE_DIR / "index.html")

            if p.startswith("/static/"):
                requested = (BASE_DIR / p.lstrip("/")).resolve()
                if not requested.is_relative_to(BASE_DIR.resolve()):
                    return self._json({"error": "forbidden"}, 403)
                return self._file(requested)

            if p == "/api/modules":
                return self._json(api_modules())

            if p.startswith("/api/modules/"):
                tail = p[len("/api/modules/") :]
                slug, _, action = tail.partition("/")
                slug = urllib.parse.unquote(slug)
                if action == "test-cases":
                    return self._json(api_test_cases(slug))
                if action == "summary":
                    data = api_summary(slug)
                    return (
                        self._json(data)
                        if data
                        else self._json({"error": "not_found"}, 404)
                    )
                if action == "custom-test-cases":
                    data = api_list_custom_cases(slug)
                    return (
                        self._json(data)
                        if data is not None
                        else self._json({"error": "not_found"}, 404)
                    )

            if p.startswith("/api/test-cases/") and p.endswith("/history"):
                tc_id = urllib.parse.unquote(
                    p[len("/api/test-cases/") : -len("/history")]
                )
                data = api_history(tc_id)
                return (
                    self._json(data)
                    if data is not None
                    else self._json({"error": "not_found"}, 404)
                )

            self._json({"error": "not_found"}, 404)
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def do_DELETE(self) -> None:  # noqa: N802
        try:
            p = urllib.parse.urlparse(self.path).path.rstrip("/")

            if p.startswith("/api/test-cases/") and p.endswith("/result"):
                tc_id = urllib.parse.unquote(
                    p[len("/api/test-cases/") : -len("/result")]
                )
                ok, err = api_clear_case(tc_id)
                if err == "not_found":
                    return self._json({"error": "Test case not found"}, 404)
                return self._json({"ok": True})

            if p.startswith("/api/custom-test-cases/"):
                raw = urllib.parse.unquote(p[len("/api/custom-test-cases/") :])
                try:
                    case_id = int(raw)
                except ValueError:
                    return self._json({"error": "invalid id"}, 400)
                ok, err = api_delete_custom_case(case_id)
                if err == "not_found":
                    return self._json({"error": "Custom test case not found"}, 404)
                return self._json({"ok": True})

            self._json({"error": "not_found"}, 404)
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def do_PATCH(self) -> None:  # noqa: N802
        try:
            p = urllib.parse.urlparse(self.path).path.rstrip("/")
            body = self._read_body()

            if p.startswith("/api/custom-test-cases/"):
                raw = urllib.parse.unquote(p[len("/api/custom-test-cases/") :])
                try:
                    case_id = int(raw)
                except ValueError:
                    return self._json({"error": "invalid id"}, 400)
                result, err = api_update_custom_case(case_id, body)
                if err == "not_found":
                    return self._json({"error": "Custom test case not found"}, 404)
                if err == "scenario_required":
                    return self._json({"error": "Scenario is required"}, 400)
                if err == "invalid_status":
                    return self._json({"error": "Invalid status value"}, 400)
                return self._json(result)

            self._json({"error": "not_found"}, 404)
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            p = urllib.parse.urlparse(self.path).path.rstrip("/")
            body = self._read_body()

            if p.startswith("/api/test-cases/") and p.endswith("/result"):
                tc_id = urllib.parse.unquote(
                    p[len("/api/test-cases/") : -len("/result")]
                )
                result, err = api_save_result(
                    tc_id,
                    body.get("status", ""),
                    body.get("notes", ""),
                )
                if err == "invalid_status":
                    return self._json({"error": "Invalid status value"}, 400)
                if err == "not_found":
                    return self._json({"error": "Test case not found"}, 404)
                return self._json(result)

            if p.startswith("/api/modules/") and p.endswith("/clear"):
                slug = urllib.parse.unquote(p[len("/api/modules/") : -len("/clear")])
                ok, err = api_clear_module(slug)
                if err == "not_found":
                    return self._json({"error": "Module not found"}, 404)
                return self._json({"ok": True})

            if p.startswith("/api/modules/") and p.endswith("/custom-test-cases"):
                slug = urllib.parse.unquote(
                    p[len("/api/modules/") : -len("/custom-test-cases")]
                )
                result, err = api_create_custom_case(slug, body)
                if err == "not_found":
                    return self._json({"error": "Module not found"}, 404)
                if err == "scenario_required":
                    return self._json({"error": "Scenario is required"}, 400)
                if err == "invalid_status":
                    return self._json({"error": "Invalid status value"}, 400)
                return self._json(result, 201)

            self._json({"error": "not_found"}, 404)
        except Exception as exc:
            self._json({"error": str(exc)}, 500)


# ── Entry point ───────────────────────────────────────────────────────────────


def _get_local_ip() -> str:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:  # nosec B110
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    print()
    print("  Resource Planner -- Test Tracker")
    print()
    print("  Initialising database...")
    init_db()
    seed_data()
    host = _get_local_ip()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("  Ready:")
    print(f"    http://localhost:{PORT}")
    print(f"    http://{host}:{PORT}")
    print("  Press Ctrl+C to stop.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
