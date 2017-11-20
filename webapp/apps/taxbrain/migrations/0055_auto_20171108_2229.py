# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webapp.apps.taxbrain.models


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0054_outputurl_webapp_vers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxsaveinputs',
            name='reform_style',
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='CTC_new_for_all',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='DependentCredit_Child_c',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='DependentCredit_Nonchild_c',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FilerCredit_c_0',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FilerCredit_c_1',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FilerCredit_c_2',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FilerCredit_c_3',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FilerCredit_c_4',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='FilerCredit_c_cpi',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_0',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_1',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_2',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_3',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_4',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_5',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_Switch_6',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_rt',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='ID_AmountCap_rt_cpi',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_EligibleRate_active',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_EligibleRate_passive',
            field=webapp.apps.taxbrain.models.CommaSeparatedField(default=None, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_top_stacking',
            field=models.CharField(default=b'True', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='taxsaveinputs',
            name='PT_wages_active_income',
            field=models.CharField(default=b'False', max_length=50, null=True, blank=True),
        ),
    ]
