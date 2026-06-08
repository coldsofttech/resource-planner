from django.urls import path

from apps.skills.views import SkillsListView

urlpatterns = [
    path("skills/", SkillsListView.as_view(), name="skills-list"),
]
