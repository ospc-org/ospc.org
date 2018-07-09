# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0030_auto_20160926_1509'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='AGI_surtax_thd_0',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='AGI_surtax_thd_1',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='AGI_surtax_thd_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='AGI_surtax_thd_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='AGI_surtax_trt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
