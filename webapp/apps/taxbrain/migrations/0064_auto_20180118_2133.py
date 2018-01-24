# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0063_auto_20180118_2125'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_prt_0',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_prt_1',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_prt_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_prt_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_prt_4',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_prt_cpi',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_thd_0',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_thd_1',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_thd_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_thd_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_thd_4',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_excl_wagelim_thd_cpi',
            field=models.NullBooleanField(default=None),
        ),
    ]
