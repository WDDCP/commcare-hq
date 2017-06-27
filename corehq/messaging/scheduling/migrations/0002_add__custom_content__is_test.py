# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-23 17:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scheduling', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_content_id', models.CharField(max_length=126)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='alertschedule',
            name='is_test',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='timedschedule',
            name='is_test',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='alertevent',
            name='custom_content',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scheduling.CustomContent'),
        ),
        migrations.AddField(
            model_name='timedevent',
            name='custom_content',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scheduling.CustomContent'),
        ),
    ]