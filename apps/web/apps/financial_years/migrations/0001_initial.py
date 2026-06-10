import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinancialYear",
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
                ("start_date", models.DateField(db_index=True)),
                ("end_date", models.DateField(db_index=True)),
                (
                    "long_fy",
                    models.CharField(db_index=True, editable=False, max_length=20),
                ),
                (
                    "short_fy",
                    models.CharField(editable=False, max_length=10),
                ),
                (
                    "span_days",
                    models.PositiveIntegerField(default=0, editable=False),
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
                ("note", models.TextField(blank=True, default="")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_financialyear_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_financialyear_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-start_date"],
                "permissions": [
                    ("import_financialyear", "Can import financial years"),
                    ("export_financialyear", "Can export financial years"),
                ],
            },
        ),
    ]
