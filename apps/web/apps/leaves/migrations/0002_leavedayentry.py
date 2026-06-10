import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leaves", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeaveDayEntry",
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
                    "date",
                    models.DateField(db_index=True),
                ),
                (
                    "is_half_day",
                    models.BooleanField(default=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "leave",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="day_entries",
                        to="leaves.leave",
                    ),
                ),
            ],
            options={
                "ordering": ["date"],
            },
        ),
        migrations.AddConstraint(
            model_name="leavedayentry",
            constraint=models.UniqueConstraint(
                fields=["leave", "date"],
                name="leaves_leavedayentry_leave_date_uniq",
            ),
        ),
    ]
