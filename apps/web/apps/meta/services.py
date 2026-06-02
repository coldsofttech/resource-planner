from apps.core.services import ContextService
from apps.meta.selectors import get_public_meta, get_user_meta


class MetaService(ContextService):
    @staticmethod
    def get_meta(user):
        data = get_public_meta()
        if user.is_authenticated:
            data["user"] = get_user_meta(user)
        return data
