# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0056_auto_20150303_1519'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='child_phase_out_threshold',
            new_name='child_phase_out_threshold_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_credit_rate',
            new_name='eitc_credit_rate_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_rate',
            new_name='eitc_phase_out_rate_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='eitc_phase_out_threshold',
            new_name='eitc_phase_out_threshold_0',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='child_phase_out_threshold_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='child_phase_out_threshold_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='child_phase_out_threshold_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_credit_rate_1',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_credit_rate_2',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_credit_rate_3',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_rate_1',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_rate_2',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_rate_3',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_threshold_1',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_threshold_2',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='eitc_phase_out_threshold_3',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
