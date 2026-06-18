from apps.configurations.selectors import Project as ProjectSizeSelector
from apps.configurations.services import AdminConfigurationService
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers.project_size_config import ProjectSizeConfigSerializer

_CONFIG_MAP = {
    "xs_max_amount": "PROJECT_SIZE_XS_MAX_AMOUNT",
    "s_max_amount": "PROJECT_SIZE_S_MAX_AMOUNT",
    "m_max_amount": "PROJECT_SIZE_M_MAX_AMOUNT",
    "l_max_amount": "PROJECT_SIZE_L_MAX_AMOUNT",
}


def _current_config() -> dict:
    return {
        "xs_max_amount": ProjectSizeSelector.get_size_xs_max_amount(),
        "s_max_amount": ProjectSizeSelector.get_size_s_max_amount(),
        "m_max_amount": ProjectSizeSelector.get_size_m_max_amount(),
        "l_max_amount": ProjectSizeSelector.get_size_l_max_amount(),
    }


class ProjectSizeConfigViewSet(BaseViewSet):
    def retrieve(self, request):
        return self.response(data=_current_config())

    def partial_update(self, request):
        serializer = ProjectSizeConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        svc = AdminConfigurationService(user=request.user, request=request)
        for field, code in _CONFIG_MAP.items():
            if field in serializer.validated_data:
                svc.set_config(config_code=code, value=serializer.validated_data[field])

        return self.response(
            data=_current_config(),
            message="Project size thresholds updated successfully.",
        )
