from django.urls import register_converter

from apps.core.apps import BaseAppConfig


class ResourcePlanConfig(BaseAppConfig):
    name = "apps.resource_plans"
    label = "resource_plans"
    verbose_name = "Resource Plans"

    def on_ready(self):
        from apps.resource_plans.converters import VersionCodeConverter

        register_converter(VersionCodeConverter, "version_code")
