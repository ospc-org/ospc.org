import pytest
import json
import time

from api import create_app

@pytest.fixture
def app():
    app = create_app({'TESTING': True})

    yield app

@pytest.fixture
def client(app):
    return app.test_client()


def test_hello(client):
    resp = client.get('/hello')
    print(resp)


def test_dropq_small_start_job(client):
    data = {
        'user_mods': '{"policy": {"2017": {"_FICA_ss_trt": [0.1]}}, "consumption": {}, "behavior": {}, "growdiff_baseline": {}, "growdiff_response": {}, "growmodel": {}}',
        'first_budget_year': 2017,
        'start_budget_year': 0,
        'use_puf_not_cps': True,
        'num_budget_years': 1,
        'year': 0
    }
    resp = client.post('/dropq_small_start_job',
                       data=data
                       )
    print(resp)
    print(('raw data', resp.data))
    data = json.loads(resp.data.encode('utf-8'))
    job_id = data['job_id']
    status = 'NO'
    tries = 30
    while status == 'NO' and tries > 0:
        resp = client.get(
            '/dropq_query_result?job_id={job_id}'.format(job_id=job_id)
        )
        status = resp.data.encode('utf-8')
        time.sleep(1)
        tries -= 1

    assert status == 'YES'

    resp = client.get(
        '/dropq_get_result?job_id={job_id}'.format(job_id=job_id)
    )
    result = json.loads(resp.data.encode('utf-8'))
    assert 'aggr_1' in result
