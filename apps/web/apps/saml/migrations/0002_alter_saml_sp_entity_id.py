from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("saml", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saml",
            name="sp_entity_id",
            field=models.URLField(blank=True),
        ),
    ]
