# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-01 18:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('private_sector_datamigration', '0006_auto_20170520_1638'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='episodeprescription',
            name='beneficiaryId',
        ),
        migrations.RemoveField(
            model_name='episodeprescription',
            name='episodeId',
        ),
        migrations.DeleteModel(
            name='EpisodePrescription',
        ),
    ]
