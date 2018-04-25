# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0031_auto_20160926_1514'),
    ]

    operations = [
        migrations.CreateModel(
            name='JSONReformTaxCalculator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=4000, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='json_text',
            field=models.ForeignKey(default=None, to='taxbrain.JSONReformTaxCalculator', null=True),
        ),
    ]
