from apps.configurations.models import Configuration


def mark_setup_complete() -> None:
    Configuration.objects.update_or_create(
        config_code="SETUP_COMPLETE",
        defaults={"value": "true", "label": "Setup Complete"},
    )
