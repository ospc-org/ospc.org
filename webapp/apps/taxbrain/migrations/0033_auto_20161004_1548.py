# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0032_auto_20161004_1216'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorMessageTaxCalculator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=4000, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='error_text',
            field=models.ForeignKey(default=None, to='taxbrain.ErrorMessageTaxCalculator', null=True),
        ),
    ]
