# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0047_auto_20170329_1954'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='ALD_Investment_ec_base_code_active',
            new_name='ALD_InvInc_ec_base_code_active',
        ),
    ]
