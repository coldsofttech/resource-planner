"""Integration tests for apps.setup.engine — DatabaseEngineService."""

from unittest.mock import MagicMock, patch

import pytest

from apps.setup.engine import DatabaseEngineService

pytestmark = pytest.mark.django_db


@pytest.fixture
def svc():
    return DatabaseEngineService(user=None, request=None)


# ---------------------------------------------------------------------------
# DatabaseEngineService.to_postgresql()
# ---------------------------------------------------------------------------


class TestDatabaseEngineToPostgresql:
    def test_calls_build_databases(self, svc):
        mock_dbs = {"default": {"NAME": "testdb"}}
        with (
            patch(
                "apps.setup.engine.build_databases", return_value=mock_dbs
            ) as mock_build,
            patch("apps.setup.engine.settings"),
            patch("apps.setup.engine.call_command"),
            patch("apps.setup.engine.connections") as mock_conn,
        ):
            mock_conn.__iter__ = MagicMock(return_value=iter([]))
            svc.to_postgresql()

        mock_build.assert_called_once()

    def test_updates_settings_databases(self, svc):
        mock_dbs = {"default": {"NAME": "testdb"}}
        with (
            patch("apps.setup.engine.build_databases", return_value=mock_dbs),
            patch("apps.setup.engine.settings") as mock_settings,
            patch("apps.setup.engine.call_command"),
            patch("apps.setup.engine.connections") as mock_conn,
        ):
            mock_conn.__iter__ = MagicMock(return_value=iter([]))
            svc.to_postgresql()

        assert mock_settings.DATABASES == mock_dbs

    def test_calls_migrate(self, svc):
        mock_dbs = {"default": {"NAME": "testdb"}}
        with (
            patch("apps.setup.engine.build_databases", return_value=mock_dbs),
            patch("apps.setup.engine.settings"),
            patch("apps.setup.engine.call_command") as mock_cmd,
            patch("apps.setup.engine.connections") as mock_conn,
        ):
            mock_conn.__iter__ = MagicMock(return_value=iter([]))
            svc.to_postgresql()

        mock_cmd.assert_called_once_with("migrate", verbosity=0)

    def test_closes_all_connections(self, svc):
        mock_dbs = {"default": {"NAME": "testdb"}}
        with (
            patch("apps.setup.engine.build_databases", return_value=mock_dbs),
            patch("apps.setup.engine.settings"),
            patch("apps.setup.engine.call_command"),
            patch("apps.setup.engine.connections") as mock_conn,
        ):
            mock_conn.__iter__ = MagicMock(return_value=iter([]))
            svc.to_postgresql()

        mock_conn.close_all.assert_called_once()

    def test_raises_validation_exception_on_migration_failure(self, svc):
        from apps.core.exceptions import ValidationException

        mock_dbs = {"default": {"NAME": "testdb"}}
        with (
            patch("apps.setup.engine.build_databases", return_value=mock_dbs),
            patch("apps.setup.engine.settings"),
            patch(
                "apps.setup.engine.call_command",
                side_effect=Exception("migration error"),
            ),
            patch("apps.setup.engine.connections") as mock_conn,
        ):
            mock_conn.__iter__ = MagicMock(return_value=iter([]))
            with pytest.raises(ValidationException, match="Database migration failed"):
                svc.to_postgresql()

    def test_migration_failure_message_includes_original_error(self, svc):
        from apps.core.exceptions import ValidationException

        mock_dbs = {"default": {"NAME": "testdb"}}
        with (
            patch("apps.setup.engine.build_databases", return_value=mock_dbs),
            patch("apps.setup.engine.settings"),
            patch(
                "apps.setup.engine.call_command",
                side_effect=Exception("column does not exist"),
            ),
            patch("apps.setup.engine.connections") as mock_conn,
        ):
            mock_conn.__iter__ = MagicMock(return_value=iter([]))
            with pytest.raises(ValidationException, match="column does not exist"):
                svc.to_postgresql()
