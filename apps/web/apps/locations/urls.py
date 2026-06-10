from django.urls import path

from apps.locations.views import LocationDetailView, LocationsListView

urlpatterns = [
    path("locations/", LocationsListView.as_view(), name="locations-list"),
    path(
        "locations/<str:code>/", LocationDetailView.as_view(), name="locations-detail"
    ),
]
