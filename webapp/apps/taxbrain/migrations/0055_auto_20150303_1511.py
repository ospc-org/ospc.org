# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0054_auto_20150303_1503'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_1',
            new_name='income_tax_threshold_1_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_2',
            new_name='income_tax_threshold_2_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_3',
            new_name='income_tax_threshold_3_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_4',
            new_name='income_tax_threshold_4_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_5',
            new_name='income_tax_threshold_5_single',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='income_tax_threshold_6',
            new_name='income_tax_threshold_6_single',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_1_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_1_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_1_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_2_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_2_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_2_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_3_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_3_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_3_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_4_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_4_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_4_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_5_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_5_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_5_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_6_head',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_6_jointly',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='income_tax_threshold_6_separately',
            field=models.FloatField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
