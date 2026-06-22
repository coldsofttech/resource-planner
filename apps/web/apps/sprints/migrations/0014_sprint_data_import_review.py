import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0013_add_review_forecast_permission"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SprintDataImportReview",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        db_index=True, editable=False, max_length=50, unique=True
                    ),
                ),
                ("reviewed_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "import_record",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="sprints.sprintdataimport",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sprint_import_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-reviewed_at"],
            },
        ),
        migrations.CreateModel(
            name="SprintDataImportReviewResult",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "check_type",
                    models.CharField(
                        choices=[
                            ("CHECK_ASSIGNEE", "Assignee"),
                            ("CHECK_SPRINT", "Sprint"),
                            ("CHECK_LABEL", "Label"),
                            ("CHECK_MAPPING", "Mapping"),
                        ],
                        db_index=True,
                        max_length=30,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("pass", "Pass"), ("fail", "Fail")],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                ("message", models.TextField(blank=True, default="")),
                (
                    "review",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="sprints.sprintdataimportreview",
                    ),
                ),
                (
                    "row",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review_results",
                        to="sprints.sprintdataimportrow",
                    ),
                ),
            ],
            options={
                "ordering": ["check_type"],
            },
        ),
    ]
