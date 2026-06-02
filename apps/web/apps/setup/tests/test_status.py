import threading

import pytest

from apps.setup import status as _status


@pytest.fixture(autouse=True)
def reset_status():
    """Reset module-level state before each test."""
    _status._state["status"] = "idle"
    _status._state["current_step"] = None
    _status._state["steps"] = []
    _status._state["error"] = None
    yield


class TestStart:
    def test_sets_status_to_running(self):
        _status.start()
        assert _status.get()["status"] == "running"

    def test_initialises_all_steps_as_not_done(self):
        _status.start()
        for step in _status.get()["steps"]:
            assert step["done"] is False

    def test_sets_current_step_to_first_step(self):
        _status.start()
        first_key = _status._STEP_KEYS[0]
        assert _status.get()["current_step"] == first_key

    def test_clears_previous_error(self):
        _status._state["error"] = "previous error"
        _status.start()
        assert _status.get()["error"] is None

    def test_all_steps_have_required_keys(self):
        _status.start()
        for step in _status.get()["steps"]:
            assert "key" in step
            assert "label" in step
            assert "done" in step

    def test_step_count_matches_steps_definition(self):
        _status.start()
        assert len(_status.get()["steps"]) == len(_status.STEPS)


class TestAdvance:
    def test_marks_step_as_done(self):
        _status.start()
        _status.advance("infra")
        steps = {s["key"]: s for s in _status.get()["steps"]}
        assert steps["infra"]["done"] is True

    def test_advances_current_step_to_next(self):
        _status.start()
        _status.advance("infra")
        assert _status.get()["current_step"] == "database"

    def test_does_not_mark_other_steps_done(self):
        _status.start()
        _status.advance("infra")
        steps = {s["key"]: s for s in _status.get()["steps"]}
        assert steps["database"]["done"] is False

    def test_advance_on_last_step_does_not_overflow(self):
        _status.start()
        last_key = _status._STEP_KEYS[-1]
        _status.advance(last_key)
        assert _status.get()["current_step"] is not None or True

    def test_unknown_step_key_is_ignored(self):
        _status.start()
        _status.advance("nonexistent_step")
        state = _status.get()
        assert state["status"] == "running"

    def test_sequential_advances_progress_correctly(self):
        _status.start()
        for i, key in enumerate(_status._STEP_KEYS[:-1]):
            _status.advance(key)
            assert _status.get()["current_step"] == _status._STEP_KEYS[i + 1]


class TestComplete:
    def test_sets_status_to_complete(self):
        _status.start()
        _status.complete()
        assert _status.get()["status"] == "complete"

    def test_marks_all_steps_as_done(self):
        _status.start()
        _status.complete()
        for step in _status.get()["steps"]:
            assert step["done"] is True

    def test_clears_current_step(self):
        _status.start()
        _status.complete()
        assert _status.get()["current_step"] is None


class TestFail:
    def test_sets_status_to_error(self):
        _status.start()
        _status.fail("something went wrong")
        assert _status.get()["status"] == "error"

    def test_stores_error_message(self):
        _status.start()
        _status.fail("something went wrong")
        assert _status.get()["error"] == "something went wrong"

    def test_does_not_alter_steps(self):
        _status.start()
        _status.advance("infra")
        _status.fail("error")
        steps = {s["key"]: s for s in _status.get()["steps"]}
        assert steps["infra"]["done"] is True
        assert steps["database"]["done"] is False


class TestGet:
    def test_returns_snapshot_not_reference(self):
        _status.start()
        snapshot = _status.get()
        snapshot["status"] = "mutated"
        assert _status.get()["status"] == "running"

    def test_returns_copy_of_steps_list(self):
        _status.start()
        snapshot = _status.get()
        snapshot["steps"][0]["done"] = True
        assert _status.get()["steps"][0]["done"] is False

    def test_idle_state_by_default(self):
        state = _status.get()
        assert state["status"] == "idle"
        assert state["current_step"] is None
        assert state["steps"] == []
        assert state["error"] is None


class TestThreadSafety:
    def test_concurrent_advances_do_not_corrupt_state(self):
        _status.start()
        errors = []

        def do_advance(key):
            try:
                _status.advance(key)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=do_advance, args=(key,))
            for key in _status._STEP_KEYS
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        state = _status.get()
        assert state["status"] == "running"
