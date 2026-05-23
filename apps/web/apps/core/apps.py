import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class BaseAppConfig(AppConfig):
    """Standardised base AppConfig for all Django apps."""

    default = False
    auto_import_signals = True
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        self._import_signals()
        self.on_ready()

    def _import_signals(self):
        """Auto-import signals.py if present."""
        if not self.auto_import_signals:
            return

        try:
            import importlib

            importlib.import_module(f"{self.name}.signals")
            logger.debug("Loaded signals for %s.", self.name)
        except ModuleNotFoundError as exc:
            if exc.name != f"{self.name}.signals":
                raise
            logger.debug("No signals module found for %s.", self.name)

    def on_ready(self):
        """Override in subclasses for custom startup behaviour."""
        pass
