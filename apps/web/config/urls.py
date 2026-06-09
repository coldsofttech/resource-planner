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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("setup/", include("apps.setup.urls")),
    path("", include("apps.auth.urls")),
    path("", include("apps.users.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.teams.urls")),
    path("", include("apps.skills.urls")),
    path("", include("apps.locations.urls")),
    path("", include("apps.employment_types.urls")),
    path("", include("apps.roles.urls")),
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
