# -*- coding: utf-8 -*-


from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0002_dynamicsaveinputs_user_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicsaveinputs',
            name='frisch',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
    ]
