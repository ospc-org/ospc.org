# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0021_auto_20160505_1445'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='ID_Charity_crt_Cash',
            new_name='ID_Charity_crt_all',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='ID_Charity_crt_Asset',
            new_name='ID_Charity_crt_noncash',
        ),
    ]
