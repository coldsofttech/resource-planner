from django.urls import path

from apps.tags.views import TagsListView

urlpatterns = [
    path("tags/", TagsListView.as_view(), name="tags-list"),
]
