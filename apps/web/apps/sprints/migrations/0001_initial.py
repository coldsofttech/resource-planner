import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("financial_years", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sprint",
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
                    "code",
                    models.CharField(
                        db_index=True,
                        editable=False,
                        max_length=50,
                        unique=True,
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
                    "is_active",
                    models.BooleanField(default=True, db_index=True),
                ),
                (
                    "sprint_number",
                    models.PositiveIntegerField(db_index=True, unique=True),
                ),
                ("name", models.CharField(db_index=True, max_length=255)),
                ("start_date", models.DateField(db_index=True)),
                ("end_date", models.DateField(db_index=True)),
                (
                    "month",
                    models.CharField(db_index=True, editable=False, max_length=7),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("in_progress", "In Progress"),
                            ("future", "Future"),
                            ("completed", "Completed"),
                            ("expired", "Expired"),
                        ],
                        db_index=True,
                        default="future",
                        max_length=20,
                    ),
                ),
                (
                    "is_overridden",
                    models.BooleanField(default=False, db_index=True),
                ),
                ("note", models.TextField(blank=True, default="")),
                (
                    "is_closed",
                    models.BooleanField(default=False, db_index=True),
                ),
                ("closed_on", models.DateTimeField(blank=True, null=True)),
                (
                    "closed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="closed_sprint_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_sprint_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "financial_year",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sprints",
                        to="financial_years.financialyear",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_sprint_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["sprint_number"],
                "permissions": [
                    ("import_sprint", "Can import sprints"),
                    ("export_sprint", "Can export sprints"),
                    ("generate_sprint", "Can generate sprints for a financial year"),
                    ("close_sprint", "Can close/lock sprints"),
                ],
            },
        ),
    ]
