# Generated by Django 4.2.6 on 2023-12-05 11:44

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserSession",
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
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ip", models.GenericIPAddressField()),
                (
                    "last_seen_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "session_key",
                    models.CharField(
                        editable=False,
                        max_length=40,
                        unique=True,
                        verbose_name="session key",
                    ),
                ),
                ("user_agent", models.CharField(max_length=200)),
                ("data", models.JSONField(default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
