# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0019_outputurl_exp_comp_datetime'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkerNodesCounter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('singleton_enforce', models.IntegerField(default=1, unique=True)),
                ('current_offset', models.IntegerField(default=0)),
            ],
        ),
    ]
