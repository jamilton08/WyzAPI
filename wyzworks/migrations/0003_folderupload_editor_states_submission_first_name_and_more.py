# Generated by Django 5.1.1 on 2025-06-10 03:01

import wyzworks.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wyzworks", "0002_device_alter_submission_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="folderupload",
            name="editor_states",
            field=models.JSONField(
                blank=True,
                default=wyzworks.models.default_editor_states,
                help_text="Stores the current state of all code editors as JSON",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="first_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="submission",
            name="last_name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
