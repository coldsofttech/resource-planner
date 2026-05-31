from rest_framework.routers import DefaultRouter

from apps.meta.api_views import MetaViewSet

router = DefaultRouter()
router.register(r"meta", MetaViewSet, basename="meta")

urlpatterns = router.urls
