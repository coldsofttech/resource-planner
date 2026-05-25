import threading

_lock = threading.Lock()

STEPS = [
    ("infra", "Writing infrastructure config"),
    ("database", "Configuring database"),
    ("logging", "Configuring logging"),
    ("admin", "Creating admin account"),
    ("app", "Saving app settings"),
    ("auth", "Configuring authentication"),
    ("storage", "Configuring storage"),
    ("email", "Saving email settings"),
    ("complete", "Finalizing setup"),
]

_STEP_KEYS = [k for k, _ in STEPS]

_state: dict = {
    "status": "idle",
    "current_step": None,
    "steps": [],
    "error": None,
}


def start() -> None:
    with _lock:
        _state["status"] = "running"
        _state["steps"] = [
            {"key": key, "label": label, "done": False} for key, label in STEPS
        ]
        _state["current_step"] = _STEP_KEYS[0]
        _state["error"] = None


def advance(step_key: str) -> None:
    with _lock:
        for s in _state["steps"]:
            if s["key"] == step_key:
                s["done"] = True
        try:
            idx = _STEP_KEYS.index(step_key)
            if idx + 1 < len(_STEP_KEYS):
                _state["current_step"] = _STEP_KEYS[idx + 1]
        except ValueError:
            pass


def complete() -> None:
    with _lock:
        _state["status"] = "complete"
        _state["current_step"] = None
        for s in _state["steps"]:
            s["done"] = True


def fail(message: str) -> None:
    with _lock:
        _state["status"] = "error"
        _state["error"] = message


def get() -> dict:
    with _lock:
        return {
            "status": _state["status"],
            "current_step": _state["current_step"],
            "steps": [dict(s) for s in _state["steps"]],
            "error": _state["error"],
        }
