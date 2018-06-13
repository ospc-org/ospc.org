# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0060_auto_20171219_2153'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_RealEstate_crt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_RealEstate_crt_cpi',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_StateLocalTax_crt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_StateLocalTax_crt_cpi',
            field=models.NullBooleanField(default=None),
        ),
    ]
