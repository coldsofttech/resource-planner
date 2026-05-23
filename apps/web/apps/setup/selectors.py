def get_setup_status():
    from apps.configurations.models import Configuration

    return Configuration.objects.filter(
        config_code="SETUP_COMPLETE", value="true"
    ).exists()
