# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0017_auto_20160229_0159'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='BE_CG_per',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='BE_CG_trn',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='BE_inc',
        ),
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='BE_sub',
        ),
    ]
