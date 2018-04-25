# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0013_auto_20151120_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_BenefitSurtax_Switch_6',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_RealEstate_HC',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
