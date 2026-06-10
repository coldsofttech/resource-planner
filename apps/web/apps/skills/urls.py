from django.urls import path

from apps.skills.views import SkillDetailView, SkillsListView

urlpatterns = [
    path("skills/", SkillsListView.as_view(), name="skills-list"),
    path("skills/<str:code>/", SkillDetailView.as_view(), name="skills-detail"),
]
