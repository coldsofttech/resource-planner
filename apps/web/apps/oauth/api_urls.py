from rest_framework.routers import DefaultRouter

from apps.oauth.api_views import OAuthViewSet

router = DefaultRouter()
router.register(r"auth/oauth", OAuthViewSet, basename="oauth")

urlpatterns = router.urls
