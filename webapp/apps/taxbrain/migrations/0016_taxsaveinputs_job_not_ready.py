# -*- coding: utf-8 -*-


from django.db import migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0015_auto_20160201_0257'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='job_not_ready',
            field=webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True),
        ),
    ]
