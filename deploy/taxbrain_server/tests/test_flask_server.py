from argparse import Namespace
import contextlib
from itertools import product
import json
import os
import tempfile
import time
import sys

import flask
from flask.testing import FlaskClient
import mock
import pytest
import requests
import requests_mock

sys.path.append(os.path.abspath('..'))
import flask_server

assert flask_server.MOCK_CELERY, 'Set MOCK_CELERY=1 to run tests for deploy repo'

@contextlib.contextmanager
def mock_redis_client():
    with mock.patch('flask_server.client') as redis:
        redis.llen = mock.MagicMock(return_value=1)
        yield redis


@contextlib.contextmanager
def mock_flask():
    flask_server.app.config['TESTING'] = True
    client = flask_server.app.test_client()
    with flask_server.app.app_context():
        args = Namespace(sleep_interval=5, ignore_cached_tickets=False)
        with flask_server.app_tracking_context(args=args):
            flask_server.app.debug = True
            yield client


@mock.patch('flask_server.btax_async.delay', return_value=Namespace(id='id1'))
def test_btax_endpoint(btax):
    with mock_flask() as client:
        with mock_redis_client() as redis:
            response = client.post('/btax_start_job',
                                   data=dict(year=2015,
                                             user_mods=json.dumps({"2015": {"elastic_gdp": 0.54}})))
            assert redis.llen.called
            assert btax.called
            assert response.status_code == 200, repr(response.data)


@mock.patch('flask_server.elasticity_gdp_task_async.delay', return_value=Namespace(id='id1'))
def test_elastic_endpoint(elastic):
    with mock_flask() as client:
        with mock_redis_client() as redis:
            response = client.post('/elastic_gdp_start_job',
                                   data=dict(year=2015,
                                             user_mods=json.dumps({"2015":{"elastic_gdp": 0.54}})))
            assert redis.llen.called
            assert elastic.called
            assert response.status_code == 200, repr(response.data)


@mock.patch('flask_server.ogusa_async.delay', return_value=Namespace(id='id1'))
def test_ogusa_start_job(ogusa):
    with mock_flask() as client:
        with mock_redis_client() as redis:
            response = client.post('/ogusa_start_job',
                                   data=dict(user_mods='{}',
                                             ogusa_params='{}'))
            assert ogusa.called
            assert response.status_code == 200, repr(response.data)


@contextlib.contextmanager
def mock_running_jobs(status):
    try:
        job = mock.MagicMock()
        job.result = 'ok'
        job.ready = mock.MagicMock()
        job.successful = mock.MagicMock()
        job.failed = mock.MagicMock()
        if status == 'ok':
            job.ready.return_value = True
            job.successful.return_value = True
            job.failed.return_value = False
        elif status == 'failed':
            job.traceback = 'failure-expected'
            job.ready.return_value = False
            job.successful.return_value = False
            job.failed.return_value = True
        else: # not ready
            job.ready.return_value = False
            job.failed.return_value = False
        running = {'abc': job}
        old = flask_server.RUNNING_JOBS
        flask_server.RUNNING_JOBS = running
        yield True
    finally:
        flask_server.RUNNING_JOBS = old


@pytest.mark.parametrize('status', ('ok', 'failed', 'not ready'))
def test_dropq_get_result(status):

    with mock_flask() as client:
        with mock_running_jobs(status):
            response = client.get('/dropq_get_result?job_id=abc')
            if status == 'not ready':
                expected = 202
            else:
                expected = 200
            assert response.status_code == expected, repr(response.data)


@contextlib.contextmanager
def patch_example():
    try:
        old = flask_server.example_async.delay
        delay = mock.MagicMock()
        delay.return_value = Namespace(id='abc',
                                       failed=lambda: False,
                                       result='ok',
                                       ready=lambda: True,
                                       successful=lambda: True,
                                       status='ok')
        flask_server.example_async.delay = delay
        yield True
    finally:
        flask_server.example_async.delay = old


def test_register_job():

    with mock_flask() as client:
        with patch_example():
            response = client.post('/example_start_job',
                                   data=dict(first_year=2017, user_mods='{}'))
            assert response.status_code == 200, repr(response.data)
            response = client.post('/register_job',
                                   data=dict(
                                       # This URL is a generator of random jsons
                                       # the only requirement for this test
                                       # is that the result is json.load-able
                                       callback='https://jsonplaceholder.typicode.com/posts',
                                       job_id='abc',
                                       params='{}'))
            assert response.status_code == 200, repr(response.data)
            assert 'registered' in json.loads(response.data), repr(response.data)
            assert 'abc' in flask_server.TRACKING_TICKETS
            status_code = 202
            while status_code == 202:
                response = client.get('/dropq_get_result?job_id=abc')
                status_code = response.status_code
            assert status_code == 200

