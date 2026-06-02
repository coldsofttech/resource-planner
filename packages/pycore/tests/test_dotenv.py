import os
from pathlib import Path

from pycore.dotenv import DotEnv


def _env(tmp_path: Path, content: str = "") -> DotEnv:
    if content:
        (tmp_path / ".env").write_text(content, encoding="utf-8")
    return DotEnv(tmp_path)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestDotEnvInit:
    def test_env_path_is_folder_dot_env(self, tmp_path):
        assert DotEnv(tmp_path)._path == tmp_path / ".env"

    def test_accepts_string_folder(self, tmp_path):
        assert DotEnv(str(tmp_path))._path == tmp_path / ".env"


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestDotEnvList:
    def test_returns_empty_dict_when_file_absent(self, tmp_path):
        assert DotEnv(tmp_path).list() == {}

    def test_returns_key_value_pairs(self, tmp_path):
        assert _env(tmp_path, "FOO=bar\nBAZ=qux\n").list() == {
            "FOO": "bar",
            "BAZ": "qux",
        }

    def test_skips_blank_lines(self, tmp_path):
        assert _env(tmp_path, "\nFOO=bar\n\n").list() == {"FOO": "bar"}

    def test_skips_comment_lines(self, tmp_path):
        assert _env(tmp_path, "# comment\nFOO=bar\n").list() == {"FOO": "bar"}

    def test_skips_lines_without_equals(self, tmp_path):
        assert _env(tmp_path, "NOEQUALSSIGN\nFOO=bar\n").list() == {"FOO": "bar"}

    def test_strips_whitespace_from_keys(self, tmp_path):
        assert "FOO" in _env(tmp_path, "  FOO  =bar\n").list()

    def test_strips_whitespace_from_values(self, tmp_path):
        assert _env(tmp_path, "FOO=  bar  \n").list()["FOO"] == "bar"

    def test_strips_double_quotes_from_values(self, tmp_path):
        assert _env(tmp_path, 'FOO="bar"\n').list()["FOO"] == "bar"

    def test_strips_single_quotes_from_values(self, tmp_path):
        assert _env(tmp_path, "FOO='bar'\n").list()["FOO"] == "bar"

    def test_partitions_on_first_equals_only(self, tmp_path):
        assert _env(tmp_path, "FOO=a=b=c\n").list()["FOO"] == "a=b=c"


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------


class TestDotEnvRead:
    def test_returns_value_for_existing_key(self, tmp_path):
        assert _env(tmp_path, "FOO=bar\n").read("FOO") == "bar"

    def test_returns_none_for_absent_key(self, tmp_path):
        assert _env(tmp_path, "FOO=bar\n").read("MISSING") is None

    def test_returns_none_when_file_absent(self, tmp_path):
        assert DotEnv(tmp_path).read("FOO") is None


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------


class TestDotEnvWrite:
    def test_creates_file_when_absent(self, tmp_path):
        DotEnv(tmp_path).write("FOO", "bar")
        assert (tmp_path / ".env").exists()

    def test_new_key_is_readable_after_write(self, tmp_path):
        env = _env(tmp_path, "FOO=bar\n")
        env.write("BAZ", "qux")
        assert env.read("BAZ") == "qux"

    def test_updates_existing_key_value(self, tmp_path):
        env = _env(tmp_path, "FOO=old\n")
        env.write("FOO", "new")
        assert env.read("FOO") == "new"

    def test_preserves_other_keys_when_updating(self, tmp_path):
        env = _env(tmp_path, "FOO=foo\nBAR=bar\n")
        env.write("FOO", "updated")
        assert env.read("BAR") == "bar"

    def test_preserves_comments_when_updating(self, tmp_path):
        env = _env(tmp_path, "# my comment\nFOO=old\n")
        env.write("FOO", "new")
        assert "# my comment" in (tmp_path / ".env").read_text()

    def test_creates_parent_directories_if_needed(self, tmp_path):
        nested = tmp_path / "a" / "b"
        DotEnv(nested).write("FOO", "bar")
        assert (nested / ".env").exists()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDotEnvDelete:
    def test_returns_true_when_key_removed(self, tmp_path):
        assert _env(tmp_path, "FOO=bar\n").delete("FOO") is True

    def test_returns_false_when_key_absent(self, tmp_path):
        assert _env(tmp_path, "FOO=bar\n").delete("MISSING") is False

    def test_returns_false_when_file_absent(self, tmp_path):
        assert DotEnv(tmp_path).delete("FOO") is False

    def test_key_is_absent_after_deletion(self, tmp_path):
        env = _env(tmp_path, "FOO=bar\n")
        env.delete("FOO")
        assert env.read("FOO") is None

    def test_preserves_other_keys_when_deleting(self, tmp_path):
        env = _env(tmp_path, "FOO=foo\nBAR=bar\n")
        env.delete("FOO")
        assert env.read("BAR") == "bar"

    def test_preserves_comments_when_deleting(self, tmp_path):
        env = _env(tmp_path, "# comment\nFOO=bar\n")
        env.delete("FOO")
        assert "# comment" in (tmp_path / ".env").read_text()


# ---------------------------------------------------------------------------
# load_environ
# ---------------------------------------------------------------------------


class TestDotEnvLoadEnviron:
    def test_loads_keys_into_os_environ(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PYCORE_TEST_KEY", raising=False)
        env = _env(tmp_path, "PYCORE_TEST_KEY=hello\n")
        env.load_environ()
        assert os.environ.get("PYCORE_TEST_KEY") == "hello"

    def test_does_not_overwrite_existing_environ_value(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PYCORE_TEST_KEY", "original")
        env = _env(tmp_path, "PYCORE_TEST_KEY=fromfile\n")
        env.load_environ()
        assert os.environ["PYCORE_TEST_KEY"] == "original"
