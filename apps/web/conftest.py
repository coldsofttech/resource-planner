from __future__ import annotations

from pathlib import Path

import pytest

_SLOW_N = 30


class _SlowTestReporter:
    """
    Collects per-test call durations and injects a slowest-N table into the HTML report.

    pytest-html 4.x removed the summary injection hooks, so we post-process the
    written HTML file directly inside pytest_sessionfinish.  xdist workers forward
    all TestReport objects back to the controller process, so this plugin receives
    every test's duration even under -n auto.
    """

    def __init__(self) -> None:
        self._durations: list[tuple[float, str]] = []

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when == "call" and hasattr(report, "duration"):
            self._durations.append((report.duration, report.nodeid))

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG002
        if not self._durations:
            return
        html_path: str | None = getattr(session.config.option, "htmlpath", None)
        if not html_path:
            return

        slowest = sorted(self._durations, key=lambda x: x[0], reverse=True)[:_SLOW_N]

        def _colour(dur: float) -> str:
            if dur > 1.0:
                return "#c0392b"
            if dur > 0.5:
                return "#e67e22"
            return "#27ae60"

        def _esc(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        rows = "".join(
            "<tr>"
            f'<td style="padding:4px 8px;text-align:right;color:#666">{i + 1}</td>'
            f'<td style="padding:4px 8px;font-family:monospace;'
            f'font-size:0.85em">{_esc(nodeid)}</td>'
            f'<td style="padding:4px 8px;text-align:right;'
            f'font-weight:600;color:{_colour(dur)}">{dur:.3f}s</td>'
            "</tr>"
            for i, (dur, nodeid) in enumerate(slowest)
        )

        section = (
            f'<h2 style="margin-top:2rem;font-family:sans-serif">'
            f"Slowest {_SLOW_N} Tests</h2>"
            '<table style="border-collapse:collapse;width:100%;'
            'margin-bottom:2rem;font-family:sans-serif">'
            "<thead><tr>"
            '<th style="padding:6px 8px;text-align:right;'
            'background:#f5f5f5;border-bottom:2px solid #ddd;width:3em">#</th>'
            '<th style="padding:6px 8px;text-align:left;'
            'background:#f5f5f5;border-bottom:2px solid #ddd">Test</th>'
            '<th style="padding:6px 8px;text-align:right;'
            'background:#f5f5f5;border-bottom:2px solid #ddd;width:8em">Duration</th>'
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )

        target = Path(html_path)
        if not target.exists():
            return
        content = target.read_text(encoding="utf-8")
        target.write_text(
            content.replace("</body>", section + "\n</body>", 1), encoding="utf-8"
        )


@pytest.fixture(autouse=True)
def _fast_password_hasher(settings) -> None:
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def pytest_configure(config: pytest.Config) -> None:
    config.pluginmanager.register(_SlowTestReporter(), "rp_slow_test_reporter")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
