# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0010_ogusaworkernodescounter'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicbehavioroutputurl',
            name='exp_comp_datetime',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0)),
        ),
        migrations.AddField(
            model_name='dynamicbehaviorsaveinputs',
            name='jobs_not_ready',
            field=webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dynamicelasticityoutputurl',
            name='exp_comp_datetime',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0)),
        ),
        migrations.AddField(
            model_name='dynamicelasticitysaveinputs',
            name='jobs_not_ready',
            field=webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True),
        ),
    ]
