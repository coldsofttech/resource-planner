from rest_framework.routers import DefaultRouter

from apps.saml.api_views import SAMLViewSet

router = DefaultRouter()
router.register(r"auth/saml", SAMLViewSet, basename="saml")

urlpatterns = router.urls
