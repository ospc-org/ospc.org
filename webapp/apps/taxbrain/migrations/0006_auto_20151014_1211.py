# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0005_outputurl_model_pk'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='factor_adjustment',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='factor_target',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
