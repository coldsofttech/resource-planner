import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("business_units", "0001_initial"),
        ("products", "0001_initial"),
        ("projects", "0024_projectactualconfig"),
    ]

    operations = [
        migrations.CreateModel(
            name="OnboardingContact",
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
                    "role",
                    models.CharField(
                        choices=[
                            ("requester", "Requester"),
                            ("accountable_executive", "Accountable Executive"),
                            ("point_of_contact", "Point of Contact"),
                        ],
                        db_index=True,
                        max_length=50,
                    ),
                ),
                ("email", models.EmailField(max_length=254)),
                (
                    "name",
                    models.CharField(blank=True, default="", max_length=255),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Onboarding",
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
                ("project_name", models.CharField(max_length=255)),
                ("requirements", models.TextField(blank=True, default="")),
                (
                    "tentative_start_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "tentative_end_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "project_code",
                    models.CharField(blank=True, default="", max_length=50),
                ),
                ("risk", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("rejected", "Rejected"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "products",
                    models.ManyToManyField(
                        blank=True,
                        related_name="onboardings",
                        to="products.product",
                    ),
                ),
                (
                    "business_unit",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="onboardings",
                        to="business_units.businessunit",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="onboardings",
                        to="projects.project",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="onboarding_requests",
                        to="projects.onboardingcontact",
                    ),
                ),
                (
                    "accountable_executive",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="onboarding_accountable",
                        to="projects.onboardingcontact",
                    ),
                ),
                (
                    "contacts",
                    models.ManyToManyField(
                        blank=True,
                        related_name="onboarding_contacts",
                        to="projects.onboardingcontact",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OnboardingAttachment",
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
                ("name", models.CharField(max_length=255)),
                (
                    "onboarding",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="projects.onboarding",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="OnboardingLink",
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
                ("url", models.URLField(max_length=500)),
                ("title", models.CharField(blank=True, default="", max_length=200)),
                (
                    "onboarding",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="links",
                        to="projects.onboarding",
                    ),
                ),
            ],
            options={"ordering": ["title", "url"]},
        ),
    ]
