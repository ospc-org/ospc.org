import pytest
from celery import chord

from api.celery_tasks import (taxbrain_elast_async,
                              taxbrain_elast_postprocess,
                              dropq_task_small_async,
                              taxbrain_postprocess)

@pytest.fixture(scope='session')
def celery_config():
    return {
        'broker_url': 'redis://localhost:6379',
        'result_backend': 'redis://localhost:6379',
        'task_serializer': 'json',
        'accept_content': ['msgpack', 'json']}

def test_elast_endpoint(celery_worker):
    elast_params = {
        'year_n': 1,
        'user_mods': {
            'policy': {2017: {'_FICA_ss_trt': [0.1]}},
            'behavior': {},
            'growdiff_response': {},
            'consumption': {},
            'growdiff_baseline': {},
            'growmodel': {}},
        'gdp_elasticity': 0.3,
        'use_puf_not_cps': False,
        'start_year': 2017,
        'use_full_sample':True,
        'return_dict': True
    }

    inputs = []
    for i in range(0, 3):
        inputs.append(dict(elast_params, **{'year_n': i}))
    compute_task = taxbrain_elast_async
    postprocess_task = taxbrain_elast_postprocess
    result = (chord(compute_task.signature(kwargs=i, serializer='msgpack')
              for i in inputs))(postprocess_task.signature(
                serializer='msgpack'))
    print(result.get())


def test_taxbrain_endpoint(celery_worker):
    tc_params = {
        'user_mods': {
            "policy": {
                2017: {"_FICA_ss_trt": [0.1]}},
            "consumption": {},
            "behavior": {},
            "growdiff_baseline": {},
            "growdiff_response": {},
            "growmodel": {}
        },
        'start_year': 2017,
        'use_puf_not_cps': False,
        'year_n': 0
    }

    inputs = []
    for i in range(0, 3):
        inputs.append(dict(tc_params, **{'year_n': i}))
    compute_task = dropq_task_small_async
    postprocess_task = taxbrain_postprocess
    result = (chord(compute_task.signature(kwargs=i, serializer='msgpack')
                    for i in inputs))(postprocess_task.signature(
                        serializer='msgpack'))
    print(result.get())
