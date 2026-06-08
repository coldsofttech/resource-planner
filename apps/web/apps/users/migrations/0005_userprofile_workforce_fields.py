import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_userprofile_theme_timezone"),
        ("employment_types", "0001_initial"),
        ("locations", "0001_initial"),
        ("roles", "0001_initial"),
        ("skills", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="display_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_profiles",
                to="locations.location",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="employment_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_profiles",
                to="employment_types.employmenttype",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="role",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="user_profiles",
                to="roles.role",
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="skills",
            field=models.ManyToManyField(
                blank=True,
                related_name="user_profiles",
                to="skills.skill",
            ),
        ),
        migrations.AlterModelOptions(
            name="userprofile",
            options={
                "ordering": ["user"],
                "permissions": [
                    ("change_user_workforce", "Can change user workforce details"),
                ],
            },
        ),
    ]
