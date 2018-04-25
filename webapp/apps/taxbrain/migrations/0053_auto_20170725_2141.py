# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0052_auto_20170628_2100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jsonreformtaxcalculator',
            name='assumption_text',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='jsonreformtaxcalculator',
            name='raw_assumption_text',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='jsonreformtaxcalculator',
            name='raw_reform_text',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='jsonreformtaxcalculator',
            name='reform_text',
            field=models.TextField(blank=True),
        ),
    ]
