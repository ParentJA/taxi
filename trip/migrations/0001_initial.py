# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-22 19:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nk', models.CharField(db_index=True, max_length=32, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('pick_up_address', models.CharField(max_length=255)),
                ('drop_off_address', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('REQUESTED', 'REQUESTED'), ('STARTED', 'STARTED'), ('IN_PROGRESS', 'IN_PROGRESS'), ('COMPLETED', 'COMPLETED')], default='REQUESTED', max_length=20)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trips_as_driver', to=settings.AUTH_USER_MODEL)),
                ('riders', models.ManyToManyField(related_name='trips_as_rider', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
