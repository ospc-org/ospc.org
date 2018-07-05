# -*- coding: utf-8 -*-


from django.db import migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0027_auto_20160926_1452'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='FST_AGI_thd_hi',
            new_name='FST_AGI_thd_hi_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='FST_AGI_thd_lo',
            new_name='FST_AGI_thd_hi_1',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_hi_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_hi_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_lo_0',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_lo_1',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_lo_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_lo_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
