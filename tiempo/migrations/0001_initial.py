# Generated by Django 5.1.1 on 2024-09-30 12:24

import django.core.validators
import django.db.models.deletion
import perms.utilities
import task.time_master
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0007_alter_organization_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchedulingModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('include_or_exclude', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='DateTimeCopyBoard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('isdate', models.IntegerField(validators=[django.core.validators.MaxValueValidator(2)])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('object_pk', models.IntegerField()),
                ('org_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='date_clipboard', to='organizations.organizationuser')),
            ],
        ),
        migrations.CreateModel(
            name='Scheduling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_schedule', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_retainer', to='tiempo.schedulingmodel')),
            ],
        ),
        migrations.CreateModel(
            name='WyzDateModel',
            fields=[
                ('scheduling_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tiempo.scheduling')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('name', models.CharField(max_length=100)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='date_models', to='organizations.organization')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='date_child', to='tiempo.wyzdatemodel')),
            ],
            options={
                'abstract': False,
            },
            bases=(perms.utilities.ParentPriorityGenerator, 'tiempo.scheduling', models.Model),
        ),
        migrations.CreateModel(
            name='WyzFloatModel',
            fields=[
                ('scheduling_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tiempo.scheduling')),
                ('name', models.CharField(max_length=100)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('duration', models.PositiveSmallIntegerField()),
                ('dates', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='floating_models', to='tiempo.wyzdatemodel')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='float_models', to='organizations.organization')),
            ],
            bases=('tiempo.scheduling', perms.utilities.ParentPriorityGenerator, task.time_master.TaskTimable, models.Model),
        ),
        migrations.CreateModel(
            name='WyzTimeModel',
            fields=[
                ('scheduling_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tiempo.scheduling')),
                ('name', models.CharField(max_length=100)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('dates', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_frames', to='tiempo.wyzdatemodel')),
            ],
            bases=('tiempo.scheduling', perms.utilities.ParentPriorityGenerator, task.time_master.TaskTimable, models.Model),
        ),
        migrations.CreateModel(
            name='Holidays',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField()),
                ('date', models.DateField()),
                ('schedule_holding', models.ManyToManyField(related_name='holidays', to='tiempo.schedulingmodel')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('name', 'date'), name='every holiday has its own day')],
            },
        ),
        migrations.CreateModel(
            name='DaysOfWeek',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=9, unique=True)),
                ('day_of_week', models.IntegerField(unique=True)),
                ('schedule_holding', models.ManyToManyField(related_name='days_of_week', to='tiempo.schedulingmodel')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('name', 'day_of_week'), name='every day of the week should be unique')],
            },
        ),
    ]
