from django.urls import path

from apps.to_do.views import ToDoListView, ToDoPreferencesView

urlpatterns = [
    path("to-do/preferences/", ToDoPreferencesView.as_view(), name="to-do-preferences"),
    path("to-do/", ToDoListView.as_view(), name="to-do-list"),
]
