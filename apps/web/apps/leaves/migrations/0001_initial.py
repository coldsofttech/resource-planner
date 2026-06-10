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
            name="Leave",
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
                        db_index=True, editable=False, max_length=50, unique=True
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
                    "start_date",
                    models.DateField(db_index=True),
                ),
                (
                    "end_date",
                    models.DateField(db_index=True),
                ),
                (
                    "is_half_day",
                    models.BooleanField(db_index=True, default=False),
                ),
                (
                    "half_day_period",
                    models.CharField(
                        blank=True,
                        choices=[("AM", "Morning (AM)"), ("PM", "Afternoon (PM)")],
                        max_length=2,
                        null=True,
                    ),
                ),
                (
                    "days",
                    models.DecimalField(decimal_places=1, default=0, max_digits=5),
                ),
                (
                    "note",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_%(class)s_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="leaves",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_%(class)s_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-start_date"],
                "permissions": [
                    ("import_leave", "Can import leaves"),
                    ("export_leave", "Can export leaves"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="leave",
            constraint=models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="leaves_leave_end_gte_start_chk",
            ),
        ),
    ]
