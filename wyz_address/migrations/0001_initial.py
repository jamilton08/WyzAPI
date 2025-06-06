# Generated by Django 5.1.1 on 2024-09-30 12:24

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='WyzAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326, unique=True)),
                ('address', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='AddressBridge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.IntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='contenttypes.contenttype')),
                ('address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bridge', to='wyz_address.wyzaddress')),
            ],
        ),
    ]
