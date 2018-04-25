# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0040_taxsaveinputs_id_benefitsurtax_em'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jsonreformtaxcalculator',
            old_name='text',
            new_name='reform_text',
        ),
        migrations.AddField(
            model_name='jsonreformtaxcalculator',
            name='assumption_text',
            field=models.CharField(max_length=4000, blank=True),
        ),
    ]
