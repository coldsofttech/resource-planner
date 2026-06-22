from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0016_sprint_data_import_review_capacity_result"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SprintDataImportReviewComplete",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("import_type", models.CharField(db_index=True, max_length=20)),
                ("completed_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("override_applied", models.BooleanField(default=False)),
                ("override_notes", models.TextField(blank=True, default="")),
                (
                    "completed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sprint_import_completions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "review",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="completions",
                        to="sprints.sprintdataimportreview",
                    ),
                ),
                (
                    "sprint",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="import_completions",
                        to="sprints.sprint",
                    ),
                ),
            ],
            options={
                "ordering": ["-completed_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="sprintdataimportreviewcomplete",
            constraint=models.UniqueConstraint(
                fields=["sprint", "import_type"],
                name="sprints_sprintdataimportreviewcomplete_sprint_import_type_uniq",
            ),
        ),
    ]
