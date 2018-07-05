# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0011_auto_20160614_1902'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dynamicbehaviorsaveinputs',
            old_name='BE_CG_per',
            new_name='BE_cg',
        ),
    ]
