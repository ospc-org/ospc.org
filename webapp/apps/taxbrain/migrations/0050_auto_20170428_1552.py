# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0049_auto_20170412_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='ALD_InvInc_ec_base_RyanBrady',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='CG_nodiff',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='CTC_new_refund_limited',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='EITC_indiv',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='taxsaveinputs',
            name='NIIT_PT_taxed',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
    ]
