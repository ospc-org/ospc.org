# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0026_auto_20160926_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_hi',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_thd_lo',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FST_AGI_trt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
