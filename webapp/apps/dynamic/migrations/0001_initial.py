# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import jsonfield.fields
from django.conf import settings
import uuidfield.fields
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicOutputUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_pk', models.IntegerField(default=None, null=True)),
                ('uuid', uuidfield.fields.UUIDField(null=True, default=None, editable=False, max_length=32, blank=True, unique=True)),
                ('ogusa_vers', models.CharField(default=None, max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DynamicSaveInputs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('g_y_annual', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('g_y_annual_cpi', models.NullBooleanField(default=None)),
                ('upsilon', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('upsilon_cpi', models.NullBooleanField(default=None)),
                ('job_ids', webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True)),
                ('first_year', models.IntegerField(default=None, null=True)),
                ('tax_result', jsonfield.fields.JSONField(default=None, null=True, blank=True)),
                ('creation_date', models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0))),
            ],
            options={
                'permissions': (('view_inputs', 'Allowed to view Taxbrain.'),),
            },
        ),
        migrations.AddField(
            model_name='dynamicoutputurl',
            name='unique_inputs',
            field=models.ForeignKey(default=None, to='dynamic.DynamicSaveInputs'),
        ),
        migrations.AddField(
            model_name='dynamicoutputurl',
            name='user',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
