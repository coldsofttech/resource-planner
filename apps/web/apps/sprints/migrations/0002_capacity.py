import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Capacity",
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
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_index=True),
                ),
                (
                    "working_days",
                    models.DecimalField(decimal_places=1, default=0, max_digits=6),
                ),
                (
                    "holiday_days",
                    models.DecimalField(decimal_places=1, default=0, max_digits=6),
                ),
                (
                    "leave_days",
                    models.DecimalField(decimal_places=1, default=0, max_digits=6),
                ),
                (
                    "net_capacity",
                    models.DecimalField(decimal_places=1, default=0, max_digits=6),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_capacity_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sprint_capacities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sprint",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="capacities",
                        to="sprints.sprint",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_capacity_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["sprint", "member"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=["sprint", "member"],
                        name="sprints_capacity_sprint_member_uniq",
                    )
                ],
            },
        ),
    ]
