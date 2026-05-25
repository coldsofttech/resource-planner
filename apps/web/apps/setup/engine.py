import logging

from config.database import build_databases
from django.conf import settings
from django.core.management import call_command
from django.db import connections

from apps.core.exceptions import ValidationException
from apps.core.services import ContextService

logger = logging.getLogger(__name__)


class DatabaseEngineService(ContextService):
    def to_postgresql(self):
        """Rebuild settings.DATABASES from the current environment and migrate.

        Called after env vars are updated so build_databases() picks up the
        new PostgreSQL credentials.  All subsequent Django ORM queries — including
        the admin-user creation and config saves that follow setup — will use
        the new connection.
        """

        new_databases = build_databases()
        settings.DATABASES = new_databases

        # ConnectionHandler.settings is a @cached_property (Django 4.x+).
        # On first DB access it stores the result in connections.__dict__['settings'],
        # which then shadows the descriptor permanently — resetting _settings alone
        # has no effect.  We must evict the cached entry from __dict__ so the
        # property re-runs against the updated settings.DATABASES on next access.
        connections._settings = None
        connections.__dict__.pop("settings", None)

        # Close existing connections then remove their wrapper objects from the
        # handler so they are recreated against the new database on next use.
        # close_all() marks wrappers as closed but leaves them in _connections;
        # without the delete step they would reconnect to the old SQLite file.
        connections.close_all()
        for alias in list(connections):
            try:
                del connections[alias]
            except KeyError:
                pass

        try:
            call_command("migrate", verbosity=0)
        except Exception as exc:
            raise ValidationException(
                f"Database migration failed after switching to PostgreSQL: {exc}"
            ) from exc

        logger.info(
            "Active database switched to PostgreSQL (%s) and migrations applied.",
            new_databases["default"].get("NAME"),
        )
