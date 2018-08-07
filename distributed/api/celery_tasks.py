import json
import os

from celery import Celery

import btax
from btax.front_end_util import runner_json_tables
import taxcalc

from collections import defaultdict


CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL',
                                   'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND',
                                       'redis://localhost:6379')

celery_app = Celery('tasks2', broker=CELERY_BROKER_URL,
                    backend=CELERY_RESULT_BACKEND)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['msgpack', 'json'],
)


def dropq_task(year_n, user_mods, first_budget_year, use_puf_not_cps=True,
               use_full_sample=True):
    print(
        'keywords to dropq',
        dict(
            year_n=year_n,
            start_year=int(first_budget_year),
            use_puf_not_cps=use_puf_not_cps,
            use_full_sample=use_full_sample,
            user_mods=user_mods
        )
    )

    raw_data = taxcalc.tbi.run_nth_year_taxcalc_model(
        year_n=year_n,
        start_year=int(first_budget_year),
        use_puf_not_cps=use_puf_not_cps,
        use_full_sample=use_full_sample,
        user_mods=user_mods
    )

    return raw_data


@celery_app.task(name='api.celery_tasks.taxbrain_postprocess')
def taxbrain_postprocess(ans):
    all_to_process = defaultdict(list)
    for year_data in ans:
        for key, value in year_data.items():
            all_to_process[key] += value
    results = taxcalc.tbi.postprocess(all_to_process)
    # Add taxcalc version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    # TODO: Make this the distributed app version, not the TC version
    results['dropq_version'] = vinfo['version']
    return json.dumps(results)


@celery_app.task(name='api.celery_tasks.dropq_task_async')
def dropq_task_async(year, user_mods, first_budget_year, use_puf_not_cps=True):
    return dropq_task(year, user_mods, first_budget_year,
                      use_puf_not_cps=use_puf_not_cps, use_full_sample=True)


@celery_app.task(name='api.celery_tasks.dropq_task_small_async')
def dropq_task_small_async(year, user_mods, first_budget_year,
                           use_puf_not_cps=True):
    return dropq_task(year, user_mods, first_budget_year,
                      use_puf_not_cps=use_puf_not_cps, use_full_sample=False)
