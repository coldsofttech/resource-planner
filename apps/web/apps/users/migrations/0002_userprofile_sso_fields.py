import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="sso_provider_content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="sso_provider_object_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="sso_uid",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="must_change_password",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="password_last_changed",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
