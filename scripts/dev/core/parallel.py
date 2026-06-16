import collections
import concurrent.futures
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import threading
import time

from ..constants import GREEN, RED, RESET, ROOT, YELLOW

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mKHJABCDEFGsu]")

_tty = sys.stdout.isatty()


def _enable_ansi_windows() -> None:
    """Enable VT100 ANSI processing on Windows so escape codes render correctly."""
    if os.name != "nt":
        return
    try:
        import ctypes

        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)
        m = ctypes.c_ulong()
        if k32.GetConsoleMode(h, ctypes.byref(m)):
            k32.SetConsoleMode(h, m.value | 0x0004)
    except Exception:  # nosec B110
        pass


def _run_cmd_buffered(cmd: str, buf: "collections.deque[str]", cwd=ROOT) -> int:
    """Run a shell command, streaming each output line into buf. Returns exit code."""
    buf.append(f"$ {cmd}")
    proc = subprocess.Popen(  # nosec B602  # nosemgrep
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for line in iter(proc.stdout.readline, ""):
        buf.append(_ANSI_RE.sub("", line.rstrip()))
    proc.wait()
    return proc.returncode


def _run_parallel_columns(tasks: dict) -> dict:
    """
    Run tasks concurrently and display live output in a columnar terminal layout.

    tasks: {name: callable(buf: deque) -> int}
    Returns: {name: exit_code}
    """
    names = list(tasks.keys())
    n = len(names)
    bufs: dict = {nm: collections.deque(maxlen=500) for nm in names}
    status: dict = {nm: "running" for nm in names}
    results: dict = {nm: None for nm in names}
    lock = threading.Lock()

    def _run_one(nm: str) -> None:
        rc = tasks[nm](bufs[nm])
        with lock:
            results[nm] = rc if rc is not None else 0
            status[nm] = "ok" if results[nm] == 0 else "fail"

    if not _tty:
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
            futs = [ex.submit(_run_one, nm) for nm in names]
            for f in concurrent.futures.as_completed(futs):
                try:
                    f.result()
                except Exception as exc:
                    print(f"Task error: {exc}")
        for nm in names:
            for line in bufs[nm]:
                print(f"[{nm.upper():<12}] {line}")
        return results

    COL_LINES = 10
    TOTAL_LINES = COL_LINES + 4
    REFRESH = 0.15

    tw = shutil.get_terminal_size((120, 24)).columns
    cw = max(26, (tw - n - 1) // n)

    _BADGE = {"running": "RUNNING", "ok": "  DONE ", "fail": "FAILED "}
    _BADGE_COL = {"running": YELLOW, "ok": GREEN, "fail": RED}

    def _pad(s: str, w: int) -> str:
        s = _ANSI_RE.sub("", s).expandtabs(4)
        return (s[: w - 1] + "~") if len(s) > w else s.ljust(w)

    def _header(nm: str) -> str:
        label = nm.upper()
        badge = _BADGE[status[nm]]
        col = _BADGE_COL[status[nm]]
        inner = cw - 2
        max_label = inner - len(badge) - 1
        if len(label) > max_label:
            label = label[:max_label]
        gap = " " * max(1, inner - len(label) - len(badge))
        return f" {label}{gap}{col}{badge}{RESET} "

    def _sep(left: str, mid: str, right: str, fill: str) -> str:
        seg = fill * cw
        return left + (seg + mid) * (n - 1) + seg + right

    def _frame() -> str:
        rows = [
            _sep("┌", "┬", "┐", "─"),
            "│" + "│".join(_header(nm) for nm in names) + "│",
            _sep("├", "┼", "┤", "─"),
        ]
        for i in range(COL_LINES):
            parts = []
            for nm in names:
                snap = list(bufs[nm])
                idx = len(snap) - COL_LINES + i
                line = snap[idx] if 0 <= idx < len(snap) else ""
                parts.append(" " + _pad(line, cw - 2) + " ")
            rows.append("│" + "│".join(parts) + "│")
        rows.append(_sep("└", "┴", "┘", "─"))
        return "\n".join(rows) + "\n"

    _enable_ansi_windows()
    sys.stdout.write("\n" + _frame())
    sys.stdout.flush()

    stop_ev = threading.Event()

    def _display_loop() -> None:
        while not stop_ev.is_set():
            with lock:
                sys.stdout.write(f"\033[{TOTAL_LINES}A\r" + _frame())
                sys.stdout.flush()
            time.sleep(REFRESH)
        with lock:
            sys.stdout.write(f"\033[{TOTAL_LINES}A\r" + _frame())
            sys.stdout.flush()

    disp = threading.Thread(target=_display_loop, daemon=True)
    disp.start()

    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:
        fut_map = {ex.submit(_run_one, nm): nm for nm in names}
        for f in concurrent.futures.as_completed(fut_map):
            try:
                f.result()
            except Exception as exc:
                nm = fut_map[f]
                with lock:
                    bufs[nm].append(f"Error: {exc}")
                    results[nm] = 1
                    status[nm] = "fail"

    stop_ev.set()
    disp.join()
    print()
    return results


def _print_status_table(columns: "dict[str, tuple[str, list[str]]]") -> None:
    """
    Print a static columnar status table using the same aesthetic
    as _run_parallel_columns.
    """
    if not columns:
        return

    names = list(columns.keys())
    n = len(names)
    _enable_ansi_windows()

    tw = shutil.get_terminal_size((120, 24)).columns
    cw = max(24, (tw - n - 1) // n)

    _STATUS_BADGE = {
        "ok": "  DONE ",
        "fail": "FAILED ",
        "starting": "STARTING",
        "running": "RUNNING",
    }
    _STATUS_COL = {
        "ok": GREEN,
        "fail": RED,
        "starting": YELLOW,
        "running": YELLOW,
    }

    def _pad(s: str, w: int) -> str:
        s = _ANSI_RE.sub("", s).expandtabs(4)
        return (s[: w - 1] + "~") if len(s) > w else s.ljust(w)

    def _header(nm: str) -> str:
        st = columns[nm][0]
        label = nm.upper()
        badge = _STATUS_BADGE.get(st, "       ")
        col = _STATUS_COL.get(st, "")
        inner = cw - 2
        max_label = inner - len(badge) - 1
        if len(label) > max_label:
            label = label[:max_label]
        gap = " " * max(1, inner - len(label) - len(badge))
        return f" {label}{gap}{col}{badge}{RESET} "

    def _sep(left: str, mid: str, right: str, fill: str) -> str:
        seg = fill * cw
        return left + (seg + mid) * (n - 1) + seg + right

    col_lines = max((len(v[1]) for v in columns.values()), default=0)
    col_lines = max(col_lines, 3)

    rows = [
        _sep("┌", "┬", "┐", "─"),
        "│" + "│".join(_header(nm) for nm in names) + "│",
        _sep("├", "┼", "┤", "─"),
    ]
    for i in range(col_lines):
        parts = []
        for nm in names:
            lines = columns[nm][1]
            line = lines[i] if i < len(lines) else ""
            parts.append(" " + _pad(line, cw - 2) + " ")
        rows.append("│" + "│".join(parts) + "│")
    rows.append(_sep("└", "┴", "┘", "─"))

    print("\n" + "\n".join(rows))


def _enter_raw_mode() -> object:
    """Put stdin into cbreak mode (raw input, but Ctrl+C still sends SIGINT)."""
    if os.name == "nt":
        return None
    try:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)  # type: ignore[attr-defined]
        tty.setcbreak(fd)  # type: ignore[attr-defined]
        return old
    except Exception:  # nosec B110
        return None


def _exit_raw_mode(old_settings: object) -> None:
    """Restore stdin from cbreak mode."""
    if os.name == "nt" or old_settings is None:
        return
    try:
        import termios

        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)  # type: ignore[attr-defined]
    except Exception:  # nosec B110
        pass


def _read_key_nonblocking() -> "str | None":
    """Return the next keypress without blocking, or None if no key is ready."""
    if os.name == "nt":
        import msvcrt  # nosec B404

        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ext = msvcrt.getwch()
            return {"K": "left", "M": "right", "H": "up", "P": "down"}.get(ext)
        return ch
    else:
        import select

        if not select.select([sys.stdin], [], [], 0)[0]:
            return None
        ch = sys.stdin.read(1)
        if ch == "\x1b" and select.select([sys.stdin], [], [], 0.02)[0]:
            seq = sys.stdin.read(2)
            return {"[D": "left", "[C": "right", "[A": "up", "[B": "down"}.get(seq)
        return ch


def _run_tab_view(tasks: dict) -> dict:
    """
    Run tasks concurrently and display their output in a switchable tab terminal view.

    Press [1]/[2]/... or Tab/arrow keys to switch tabs.
    tasks: {name: callable(buf: deque) -> int}
    Returns: {name: exit_code}
    """
    if not _tty:
        return _run_parallel_columns(tasks)

    names = list(tasks.keys())
    bufs: dict = {nm: collections.deque(maxlen=5000) for nm in names}
    status: dict = {nm: "running" for nm in names}
    results: dict = {nm: None for nm in names}
    lock = threading.Lock()
    done_ev = threading.Event()
    active = [0]
    scroll_offsets: dict = {nm: 0 for nm in names}

    def _run_one(nm: str) -> None:
        rc = tasks[nm](bufs[nm])
        with lock:
            results[nm] = rc if rc is not None else 0
            status[nm] = "ok" if results[nm] == 0 else "fail"
            if all(status[n] != "running" for n in names):
                done_ev.set()

    for nm in names:
        threading.Thread(target=_run_one, args=(nm,), daemon=True).start()

    _BADGE = {"running": "RUNNING", "ok": "  DONE ", "fail": "FAILED "}
    _BADGE_COL = {"running": YELLOW, "ok": GREEN, "fail": RED}
    _BOLD = "\033[1m" if _tty else ""

    initialized = [False]

    def _draw() -> None:
        tw, th = shutil.get_terminal_size((120, 24))
        content_h = max(th - 6, 4)
        inner_w = tw - 4

        # Tab bar
        tab_parts = []
        for i, nm in enumerate(names):
            st = status[nm]
            badge = _BADGE.get(st, "       ")
            bc = _BADGE_COL.get(st, "")
            arrow = (
                f"{_BOLD}▶ {nm.upper()}{RESET}" if i == active[0] else f"  {nm.upper()}"
            )
            tab_parts.append(f"{arrow} [{bc}{badge}{RESET}]")
        tab_bar_raw = "  │  ".join(tab_parts)
        tab_pad = max(0, tw - 2 - len(_ANSI_RE.sub("", tab_bar_raw)))

        # Content: active tab buffer, respecting scroll offset
        nm = names[active[0]]
        snap = list(bufs[nm])
        offset = scroll_offsets[nm]
        if offset == 0:
            display = snap[-content_h:] if len(snap) >= content_h else snap
        else:
            end = max(0, len(snap) - offset)
            start = max(0, end - content_h)
            display = snap[start:end]
        content_lines: list[str] = []
        for raw in display:
            clean = _ANSI_RE.sub("", raw).expandtabs(4)
            if len(clean) > inner_w:
                clean = clean[: inner_w - 1] + "~"
            content_lines.append(clean.ljust(inner_w))
        while len(content_lines) < content_h:
            content_lines.append(" " * inner_w)

        # Footer
        hints = "  ".join(f"[{i + 1}] {n}" for i, n in enumerate(names))
        hints += "  [Tab] cycle  [↑↓] scroll"
        active_offset = scroll_offsets[names[active[0]]]
        if active_offset > 0:
            hints += f"  [+{active_offset} lines]"
        hints += "  Ctrl+C to stop"
        if len(hints) > inner_w:
            hints = hints[: inner_w - 1] + "~"
        hints = hints.ljust(inner_w)

        sep = "─" * (tw - 2)
        rows = [
            "┌" + sep + "┐",
            "│" + tab_bar_raw + " " * tab_pad + "│",
            "├" + sep + "┤",
            *("│ " + cl + " │" for cl in content_lines),
            "├" + sep + "┤",
            "│ " + hints + " │",
            "└" + sep + "┘",
        ]

        # Use absolute cursor positioning for every row so that no \n is
        # emitted — \n at the terminal bottom causes scrolling and frame drift.
        out: list[str] = []
        if not initialized[0]:
            out.append("\033[2J")  # clear screen once on first paint
            initialized[0] = True
        for idx, row in enumerate(rows):
            out.append(f"\033[{idx + 1};1H{row}\033[K")
        # Erase anything below the frame from a previous (taller) draw.
        out.append(f"\033[{len(rows) + 1};1H\033[J")
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    _enable_ansi_windows()
    old_term = _enter_raw_mode()
    try:
        sys.stdout.write("\033[?25l")  # hide cursor to suppress render flicker
        sys.stdout.flush()
        REFRESH = 0.12
        while not done_ev.is_set():
            ch = _read_key_nonblocking()
            if ch is not None:
                if ch.isdigit() and 1 <= int(ch) <= len(names):
                    active[0] = int(ch) - 1
                    scroll_offsets[names[active[0]]] = 0
                elif ch in ("\t", "right"):
                    active[0] = (active[0] + 1) % len(names)
                    scroll_offsets[names[active[0]]] = 0
                elif ch == "left":
                    active[0] = (active[0] - 1) % len(names)
                    scroll_offsets[names[active[0]]] = 0
                elif ch == "up":
                    nm_active = names[active[0]]
                    _, th_cur = shutil.get_terminal_size((120, 24))
                    ch_cur = max(th_cur - 6, 4)
                    max_off = max(0, len(bufs[nm_active]) - ch_cur)
                    scroll_offsets[nm_active] = min(
                        scroll_offsets[nm_active] + 1, max_off
                    )
                elif ch == "down":
                    nm_active = names[active[0]]
                    scroll_offsets[nm_active] = max(0, scroll_offsets[nm_active] - 1)
            _draw()
            time.sleep(REFRESH)
        _draw()
    except KeyboardInterrupt:
        raise
    finally:
        sys.stdout.write("\033[?25h")  # restore cursor
        _exit_raw_mode(old_term)
        sys.stdout.write("\n")
        sys.stdout.flush()

    return results
