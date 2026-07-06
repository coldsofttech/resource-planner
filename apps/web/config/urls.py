"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import bad_request, page_not_found, permission_denied, server_error

handler400 = bad_request
handler403 = permission_denied
handler404 = page_not_found
handler500 = server_error

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("setup/", include("apps.setup.urls")),
    path("", include("apps.auth.urls")),
    path("", include("apps.users.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.teams.urls")),
    path("", include("apps.skills.urls")),
    path("", include("apps.locations.urls")),
    path("", include("apps.employment_types.urls")),
    path("", include("apps.roles.urls")),
    path("", include("apps.financial_years.urls")),
    path("", include("apps.holidays.urls")),
    path("", include("apps.leaves.urls")),
    path("", include("apps.sprints.urls")),
    path("", include("apps.projects.urls")),
    path("", include("apps.business_units.urls")),
    path("", include("apps.tags.urls")),
    path("", include("apps.recharges.urls")),
    path("", include("apps.how_to.urls")),
    path("", include("apps.configurations.urls")),
    path("", include("apps.notifications.urls")),
    path("api/v1/", include("apps.setup.api_urls")),
    path("api/v1/", include("apps.meta.api_urls")),
    path("api/v1/", include("apps.auth.api_urls")),
    path("api/v1/", include("apps.users.api_urls")),
    path("api/v1/", include("apps.oauth.api_urls")),
    path("api/v1/", include("apps.saml.api_urls")),
    path("api/v1/", include("apps.permissions.api_urls")),
    path("api/v1/", include("apps.teams.api_urls")),
    path("api/v1/", include("apps.skills.api_urls")),
    path("api/v1/", include("apps.locations.api_urls")),
    path("api/v1/", include("apps.employment_types.api_urls")),
    path("api/v1/", include("apps.roles.api_urls")),
    path("api/v1/", include("apps.financial_years.api_urls")),
    path("api/v1/", include("apps.holidays.api_urls")),
    path("api/v1/", include("apps.leaves.api_urls")),
    path("api/v1/", include("apps.sprints.api_urls")),
    path("api/v1/", include("apps.projects.api_urls")),
    path("api/v1/", include("apps.business_units.api_urls")),
    path("api/v1/", include("apps.tags.api_urls")),
    path("api/v1/", include("apps.recharges.api_urls")),
    path("api/v1/", include("apps.configurations.api_urls")),
    path("api/v1/", include("apps.notifications.api_urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path("_errors/400/", bad_request, name="test-400"),
        path("_errors/403/", permission_denied, name="test-403"),
        path("_errors/404/", page_not_found, name="test-404"),
        path("_errors/500/", server_error, name="test-500"),
    ]
