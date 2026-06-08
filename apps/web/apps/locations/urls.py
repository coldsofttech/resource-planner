from django.urls import path

from apps.locations.views import LocationsListView

urlpatterns = [
    path("locations/", LocationsListView.as_view(), name="locations-list"),
]
