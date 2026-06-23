from __future__ import annotations

import decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0019_alter_sprintdataimportreviewresult_check_type"),
        ("teams", "0005_alter_assignment_created_by_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SprintDataImportConfirmed",
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
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("import_type", models.CharField(db_index=True, max_length=20)),
                (
                    "story_type",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("jira_id", models.CharField(blank=True, default="", max_length=255)),
                ("title", models.CharField(blank=True, default="", max_length=500)),
                ("assignee", models.CharField(blank=True, default="", max_length=255)),
                ("efforts", models.CharField(blank=True, default="", max_length=100)),
                (
                    "days",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0"),
                        max_digits=10,
                    ),
                ),
                ("label", models.CharField(blank=True, default="", max_length=255)),
                ("mapping", models.CharField(blank=True, default="", max_length=255)),
                (
                    "sprint",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_import_confirmed",
                        to="sprints.sprint",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sprint_data_import_confirmed",
                        to="teams.team",
                    ),
                ),
                (
                    "import_record",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="confirmed_rows",
                        to="sprints.sprintdataimport",
                    ),
                ),
            ],
            options={
                "ordering": ["pk"],
            },
        ),
    ]
