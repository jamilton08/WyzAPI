# Generated by Django 5.1.1 on 2025-06-26 04:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wyzworks", "0006_completedfield_default_props_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="completedfield",
            name="gradable",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="completedfield",
            name="points",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
