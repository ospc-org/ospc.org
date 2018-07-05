# -*- coding: utf-8 -*-


from django.db import models, migrations
import datetime
from django.conf import settings
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BTaxOutputUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_pk', models.IntegerField(default=None, null=True)),
                ('exp_comp_datetime', models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0))),
                ('uuid', models.UUIDField(null=True, default=None, editable=False, max_length=32, blank=True, unique=True)),
                ('btax_vers', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('taxcalc_vers', models.CharField(default=None, max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='BTaxSaveInputs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('btax_betr_corp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_betr_entity_Switch', models.NullBooleanField(default=None)),
                ('btax_betr_pass', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_allyr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_3yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_5yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_7yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_10yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_15yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_20yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_25yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_27_5yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_39yr', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('btax_depr_allyr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_3yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_5yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_7yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_10yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_15yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_20yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_25yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_27_5yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_39yr_gds_Switch', models.CharField(default=b'True', max_length=50, null=True, blank=True)),
                ('btax_depr_allyr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_3yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_5yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_7yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_10yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_15yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_20yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_25yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_27_5yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_39yr_ads_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_allyr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_3yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_5yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_7yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_10yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_15yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_20yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_25yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_27_5yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_39yr_tax_Switch', models.CharField(default=b'False', max_length=50, null=True, blank=True)),
                ('btax_depr_allyr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_3yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_5yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_7yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_10yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_15yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_20yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_25yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_27_5yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_depr_39yr_exp', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_other_hair', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_other_corpeq', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_other_proptx', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_other_invest', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_econ_nomint', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('btax_econ_inflat', webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True)),
                ('job_ids', webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True)),
                ('jobs_not_ready', webapp.apps.taxbrain.models.SeparatedValuesField(default=None, null=True, blank=True)),
                ('first_year', models.IntegerField(default=None, null=True)),
                ('tax_result', models.TextField(default=None, null=True, blank=True)),
                ('creation_date', models.DateTimeField(default=datetime.datetime(2015, 1, 1, 0, 0))),
            ],
            options={
                'permissions': (('view_inputs', 'Allowed to view Taxbrain.'),),
            },
        ),
        migrations.AddField(
            model_name='btaxoutputurl',
            name='unique_inputs',
            field=models.ForeignKey(default=None, to='btax.BTaxSaveInputs'),
        ),
        migrations.AddField(
            model_name='btaxoutputurl',
            name='user',
            field=models.ForeignKey(default=None, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
