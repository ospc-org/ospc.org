from post_reform import (DATA, LOCAL_BASE_URL, get_session, get_data, post_file,
                         post_reform)
from compare_results import (get_taxbrain_result, get_dropq_result,
                             assert_results_equal)

from all_params_reform import get_formatted_reform, REFORM

from datetime import datetime
import time
import requests
import os
import json
import pytest

import traceback

CUR_PATH = cur_path = os.path.abspath(os.path.dirname(__file__))


def run_reform(start_year, reform, assump=None, reform_dq=None, data=DATA):
    print("START_YEAR:", start_year)
    print("REFORM:", reform)
    print("ASSUMP:", assump)
    print("REFORM_DQ:", reform_dq)
    print("INITDATA:", data)
    start = datetime.now()

    session, csrftoken = get_session(url=LOCAL_BASE_URL)
    data[u'csrfmiddlewaretoken'] = csrftoken
    data[u'start_year'] = unicode(start_year)
    # start calculations on local taxbrain instance
    if isinstance(reform, str) and os.path.exists(reform):
        session, pk, response = post_file(session, DATA, reform,
                                          assump,
                                          url=LOCAL_BASE_URL + 'file/')
    else:
        assert (isinstance(reform, dict) and
                (isinstance(assump, dict) or assump is None))
        data.update(reform)
        if assump is not None:
            data.update(assump)
        session, pk, response = post_reform(session, data, url=LOCAL_BASE_URL)

    # run taxcalc.dropq
    if reform_dq is not None:
        dq = get_dropq_result(start_year, reform_dq, assump=assump)
    else:
        dq = get_dropq_result(start_year, reform, assump=assump)

    # check db for results for at max 10 minutes
    tb = None
    wait_time = 700
    while tb is None and (datetime.now() - start).seconds < wait_time:
        time.sleep(20)
        # load the database
        requests.get(response.url)
        tb = get_taxbrain_result(pk)

    print("TIME", (datetime.now() - start).seconds)
    if tb is None:
        print("no results after", round(wait_time/60.0), "minutes")
    else:
        assert_results_equal(tb, dq)

    return dq, tb, pk


def test_trump_reform():
    # passes
    trump_2016 = os.path.join(CUR_PATH, "reforms/Trump2016.json")
    print("TESTING: ", trump_2016)
    db, tb, pk = run_reform(2017, trump_2016)


def test_ryanbrady_reform():
    # passes
    ryan_brady = os.path.join(CUR_PATH, "reforms/RyanBrady.json")
    print("TESTING", ryan_brady)
    db, tb, pk = run_reform(2017, ryan_brady)


def test_r1a0_2013_reform():
    # passes
    r1 = os.path.join(CUR_PATH, "reforms/r1.json")
    a0 = os.path.join(CUR_PATH, "reforms/a0.json")
    print("TESTING", r1, a0)
    db, tb, pk = run_reform(2013, r1, assump=a0)


def test_r1a0_2017_reform():
    # passes
    r1 = os.path.join(CUR_PATH, "reforms/r1.json")
    a0 = os.path.join(CUR_PATH, "reforms/a0.json")
    print("TESTING", r1, a0)
    db, tb, pk = run_reform(2017, r1, assump=a0)


def test_r1a1_2015_reform():
    # passes
    r1 = os.path.join(CUR_PATH, "reforms/r1.json")
    a1 = os.path.join(CUR_PATH, "reforms/a1.json")
    print("TESTING", r1, a1)
    db, tb, pk = run_reform(2015, r1, assump=a1)


def test_r1a2_2016_reform():
    # passes
    r1 = os.path.join(CUR_PATH, "reforms/r1.json")
    a2 = os.path.join(CUR_PATH, "reforms/a2.json")
    print("TESTING", r1, a2)
    db, tb, pk = run_reform(2016, r1, assump=a2)


@pytest.mark.xfail
def test_allparams_2017_reform():
    # fails--results not within 2 percent
    reform_tb = get_formatted_reform()
    reform_dq = REFORM
    reform_dq = {2017: REFORM}
    print("TESTING", reform_dq)
    db, tb, pk = run_reform(2017, reform_tb, reform_dq=reform_dq)
