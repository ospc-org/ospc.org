# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import uuid

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dynamic', '0008_auto_20160222_1942'),
    ]

    operations = [
        migrations.CreateModel(
            name='DynamicElasticityOutputUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_pk', models.IntegerField(default=None, null=True)),
                ('uuid', models.UUIDField(null=True, default=None, editable=False, max_length=32, blank=True, unique=True)),
                ('taxcalc_vers', models.CharField(default=None, max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.RenameField(
            model_name='dynamicelasticitysaveinputs',
            old_name='EGDP_amtr',
            new_name='elastic_gdp',
        ),
        migrations.AddField(
            model_name='dynamicelasticityoutputurl',
            name='unique_inputs',
            field=models.ForeignKey(default=None, to='dynamic.DynamicElasticitySaveInputs'),
        ),
        migrations.AddField(
            model_name='dynamicelasticityoutputurl',
            name='user',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
