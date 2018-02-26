# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import webapp.apps.taxbrain.models
import django.db.models.deletion
from django.conf import settings
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0015_auto_20160201_0257'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dynamic', '0007_dynamicsaveinputs_guids'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicBehaviorOutputUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_pk', models.IntegerField(default=None, null=True)),
                ('uuid', models.UUIDField(null=True, default=None, editable=False, max_length=32, blank=True, unique=True)),
                ('taxcalc_vers', models.CharField(default=None, max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DynamicBehaviorSaveInputs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('BE_inc', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('BE_sub', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('BE_CG_per', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('BE_CG_trn', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('job_ids', webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True)),
                ('first_year', models.IntegerField(default=None, null=True)),
                ('tax_result', models.TextField(default=None, null=True, blank=True)),
                ('creation_date', models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0))),
                ('micro_sim', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxbrain.OutputUrl', null=True)),
            ],
            options={
                'permissions': (('view_inputs', 'Allowed to view Taxbrain.'),),
            },
        ),
        migrations.CreateModel(
            name='DynamicElasticitySaveInputs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('EGDP_amtr', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('job_ids', webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True)),
                ('first_year', models.IntegerField(default=None, null=True)),
                ('tax_result', models.TextField(default=None, null=True, blank=True)),
                ('creation_date', models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0))),
                ('micro_sim', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxbrain.OutputUrl', null=True)),
            ],
            options={
                'permissions': (('view_inputs', 'Allowed to view Taxbrain.'),),
            },
        ),
        migrations.AddField(
            model_name='dynamicbehavioroutputurl',
            name='unique_inputs',
            field=models.ForeignKey(default=None, to='dynamic.DynamicBehaviorSaveInputs'),
        ),
        migrations.AddField(
            model_name='dynamicbehavioroutputurl',
            name='user',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
