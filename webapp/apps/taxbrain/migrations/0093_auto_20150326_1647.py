# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0092_outputurl_taxcalc_vers'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='ID_medical_frt',
            new_name='ID_Medical_frt',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='FICA_trt',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='AMED_thd_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='CG_thd1_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='CG_thd2_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='CTC_c_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='CTC_ps_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='Dividend_thd1_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='Dividend_thd2_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='Dividend_thd3_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FEI_ec_c_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FICA_mc_trt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FICA_ss_trt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='NIIT_thd_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='SS_thd50_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='SS_thd85_cpi',
            field=models.NullBooleanField(default=None),
            preserve_default=True,
        ),
    ]
