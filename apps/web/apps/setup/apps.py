import logging

from apps.core.apps import BaseAppConfig

logger = logging.getLogger(__name__)


def patch_allowed_hosts():
    try:
        from urllib.parse import urlparse

        from django.conf import settings

        from apps.configurations.selectors import General

        cfg = General.get_app_url()
        logger.debug("Application URL is %s.", cfg)
        if not cfg:
            return

        logger.debug(
            "Allowed hosts before updating application url: %s.", settings.ALLOWED_HOSTS
        )
        host = urlparse(cfg).netloc  # strips scheme + path
        if host and host not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append(host)
            logger.debug(
                "Allowed hosts after updating application url: %s.",
                settings.ALLOWED_HOSTS,
            )
    except Exception:  # nosec B110
        pass  # DB not ready (pre-migration), skip silently


class SetupConfig(BaseAppConfig):
    name = "apps.setup"
    label = "setup"
    verbose_name = "Setup"

    def on_ready(self):
        from django.core.signals import request_started

        def _patch_once(**kwargs):
            patch_allowed_hosts()
            request_started.disconnect(_patch_once)

        request_started.connect(_patch_once)
