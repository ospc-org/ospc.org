# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0004_dynamicsaveinputs_micro_sim'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dynamicsaveinputs',
            name='micro_sim',
        ),
    ]
