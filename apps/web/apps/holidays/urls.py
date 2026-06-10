from django.urls import path

from apps.holidays.views import HolidaysListView

urlpatterns = [
    path("holidays/", HolidaysListView.as_view(), name="holidays-list"),
]
