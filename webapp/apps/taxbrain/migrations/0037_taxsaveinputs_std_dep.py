# -*- coding: utf-8 -*-


from django.db import migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0036_auto_20161115_2128'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxsaveinputs',
            name='STD_Dep',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
