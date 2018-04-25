# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0014_auto_20151124_2029'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='BE_cg_per',
            new_name='BE_CG_per',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='BE_cg_trn',
            new_name='BE_CG_trn',
        ),
    ]
