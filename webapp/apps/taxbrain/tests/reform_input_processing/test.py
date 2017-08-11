from post_reform import (DATA, LOCAL_BASE_URL, get_session, get_data, post_file,
                         post_reform)
from compare_results import (get_taxbrain_result, get_dropq_result,
                             assert_results_equal)

from all_params_reform import get_formatted_reform, REFORM

from datetime import datetime
import time
import requests
import os

import traceback

def test_full_run(start_year, reform, assump=None, reform_dq=None, data=DATA):
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
        dq = get_dropq_result(2017, reform_dq, assump=assump)
    else:
        dq = get_dropq_result(2017, reform, assump=assump)

    # check db for results for at max 10 minutes
    tb = None
    while tb is None and (datetime.now() - start).seconds < 600:
        time.sleep(20)
        # load the database
        requests.get(response.url)
        tb = get_taxbrain_result(pk)

    print("TIME", (datetime.now() - start).seconds)
    if tb is None:
        print("no results after 5 minutes")
    else:
        try:
            assert_results_equal(tb, dq)
        except AssertionError:
            traceback.print_exc()

if __name__ == "__main__":
    #
    # trump_2016 = "/Users/henrydoupe/Documents/Tax-Calculator/taxcalc/reforms/Trump2016.json"
    # print("TESTING: ", trump_2016)
    # test_full_run(2017, trump_2016)
    #
    # ryan_brady = "/Users/henrydoupe/Documents/Tax-Calculator/taxcalc/reforms/RyanBrady.json"
    # print("TESTING", ryan_brady)
    # test_full_run(2017, ryan_brady)

    # r1 = "/Users/henrydoupe/Documents/Tax-Calculator/file-upload-tests/r1.json"
    # a0 = "/Users/henrydoupe/Documents/Tax-Calculator/file-upload-tests/a0.json"
    # print("TESTING", r1, a0)
    # test_full_run(2017, r1, assump=a0)

    # r1 = "/Users/henrydoupe/Documents/Tax-Calculator/file-upload-tests/r1.json"
    # a1 = "/Users/henrydoupe/Documents/Tax-Calculator/file-upload-tests/a1.json"
    # print("TESTING", r1, a1)
    # test_full_run(2015, r1, assump=a1)
    #
    # r1 = "/Users/henrydoupe/Documents/Tax-Calculator/file-upload-tests/r1.json"
    # a2 = "/Users/henrydoupe/Documents/Tax-Calculator/file-upload-tests/a2.json"
    # print("TESTING", r1, a2)
    # test_full_run(2023, r1, assump=a2)
    #
    reform_tb = get_formatted_reform()
    reform_dq = REFORM
    reform_dq = {2017: REFORM}
    print("TESTING", reform_dq)
    test_full_run(2017, reform_tb, reform_dq=reform_dq)
