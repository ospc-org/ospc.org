import pytest
import json
import time
import msgpack

from api import create_app


@pytest.fixture
def taxcalc_inputs():
    return [{
        'user_mods': {
            "policy": {
                2017: {"_FICA_ss_trt": [0.1]}},
            "consumption": {},
            "behavior": {},
            "growdiff_baseline": {},
            "growdiff_response": {},
            "growmodel": {}
        },
        'first_budget_year': 2017,
        'use_puf_not_cps': True,
        'year': 0
    }]


@pytest.fixture
def app():
    app = create_app({'TESTING': True})

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def post_and_poll(client, url, data, exp_status='YES', tries=30):
    packed = msgpack.dumps({'inputs': data}, use_bin_type=True)
    resp = client.post(url,
                       data=packed,
                       headers={'Content-Type': 'application/octet-stream'}
                       )
    assert resp.status_code == 200
    data = json.loads(resp.data.decode('utf-8'))
    job_id = data['job_id']
    status = 'NO'
    while status == 'NO' and tries > 0:
        resp = client.get(
            '/dropq_query_result?job_id={job_id}'.format(job_id=job_id)
        )
        status = resp.data.decode('utf-8')
        assert resp.status_code == 200
        time.sleep(1)
        tries -= 1

    assert status == exp_status

    resp = client.get(
        '/dropq_get_result?job_id={job_id}'.format(job_id=job_id)
    )
    assert resp.status_code == 200
    return resp


def test_hello(client):
    resp = client.get('/hello')
    print(resp)


def test_dropq_small_start_job(client, taxcalc_inputs):
    resp = post_and_poll(client, '/dropq_small_start_job', taxcalc_inputs)
    result = json.loads(resp.data.decode('utf-8'))
    assert 'aggr_1' in result


def test_dropq_job_fails(client, taxcalc_inputs):
    del taxcalc_inputs[0]['user_mods']['policy']
    resp = post_and_poll(client, '/dropq_start_job', exp_status='FAIL',
                         data=taxcalc_inputs)

    assert 'Traceback' in resp.data.decode('utf-8')
