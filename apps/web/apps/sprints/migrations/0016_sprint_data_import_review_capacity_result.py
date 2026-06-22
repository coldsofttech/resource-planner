from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0015_alter_sprintdataimportreview_id_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SprintDataImportReviewCapacityResult",
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
                (
                    "allocated_days",
                    models.DecimalField(decimal_places=2, default=0, max_digits=8),
                ),
                (
                    "net_capacity",
                    models.DecimalField(decimal_places=1, default=0, max_digits=6),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("pass", "Pass"), ("fail", "Fail")],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sprint_import_capacity_results",
                        to=settings.AUTH_USER_MODEL,
                        db_index=True,
                    ),
                ),
                (
                    "review",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="capacity_results",
                        to="sprints.sprintdataimportreview",
                    ),
                ),
            ],
            options={
                "ordering": ["member__first_name", "member__last_name"],
                "unique_together": {("review", "member")},
            },
        ),
    ]
