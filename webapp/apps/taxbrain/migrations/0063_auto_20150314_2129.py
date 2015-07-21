# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taxbrain', '0062_auto_20150314_2128'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medicare_additional_threshold_single',
            new_name='_AMED_thd_0',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medicare_additional_threshold_jointly',
            new_name='_AMED_thd_1',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medicare_additional_threshold_head',
            new_name='_AMED_thd_2',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medicare_additional_threshold_separately',
            new_name='_AMED_thd_3',
        ),
        migrations.RenameField(
            model_name='taxsaveinputs',
            old_name='medicare_additional_rate',
            new_name='_AMED_trt',
        ),
    ]
