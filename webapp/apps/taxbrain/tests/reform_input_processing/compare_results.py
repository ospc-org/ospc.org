from post_reform import (get_session, get_data, get_session,
                         LOCAL_BASE_URL, TEST_BASE_URL)

from taxcalc import Calculator
from taxcalc.dropq import run_nth_year_tax_calc_model

import sqlite3
import json
import numpy as np
import pandas as pd
import os

cur_path = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(cur_path, "../../../../../db.sqlite3")
PUF_PATH = os.path.join(cur_path, "../../../../../deploy/taxbrain_server/puf.csv")
PUF = pd.read_csv(PUF_PATH)


def get_taxbrain_result(pk, db_path=DB_PATH):
    """
    get results from local sqlite3 table with primary key pk
    """
    db = sqlite3.connect(db_path)
    cursor = db.cursor()

    cursor.execute("""select tax_result
                      from taxbrain_taxsaveinputs
                      where id=={pk};""".format(pk=pk))
    res = cursor.fetchone()
    db.close()
    if res is not None and isinstance(res[0], (unicode, str)):
        return json.loads(res[0])
    else:
        return None

def get_dropq_result(start_year, reform, assump=None, taxrec_df=PUF):
    """
    get and format dropq results in a way corresponding to taxbrain
    """
    file_params = {}
    if isinstance(reform, str) and os.path.exists(reform):
        file_params = Calculator.read_json_param_files(reform, assump, False)

    # need to handle case where other files are supplied
    user_mods = {'growdiff_response': {}, 'consumption': {},
                 'growdiff_baseline': {}, 'behavior': {},
                 'gdp_elasticity': {}, 'policy': {}}

    if file_params is not None:
        for k in file_params:
            user_mods[k] = file_params[k]
    else:
        user_mods['policy'] = reform
        if assump is not None:
            user_mods.update(assump)

    # dropq results list
    res_names = ["mY_dec", "mX_dec", "df_dec", "pdf_dec", "cdf_dec",
                 "mY_bin", "mX_bin", "df_bin", "pdf_bin", "cdf_bin"]
    # need to do additional formatting for these variables
    res_fisc_names = ["fiscal_tot_diffs", "fiscal_tot_base",
                      "fiscal_tot_ref"]
    # store dropq results needing extra formatting
    res_fisc = [{"payroll_tax": [],
                 "combined_tax": [],
                 "ind_tax": []} for fn in res_fisc_names]
    # store formatted dropq results
    results = {rn: {} for rn in res_names}

    # get dropq results for next 10 years or until 2026
    for year in np.arange(0, min(10, 2026-start_year+1)):
        kw = dict(year_n=year, start_year=start_year, taxrec_df=taxrec_df,
                  user_mods=user_mods)

        dq_res = run_nth_year_tax_calc_model(**kw)

        # add results that are already formatted
        for i in range(len(res_names)):
            results[res_names[i]].update(dq_res[i])

        # loop over fiscal_* variables, store in list of dictionaries
        # corresponding to variables in res_fisc_names
        for i in range(len(res_fisc)):
            # only want the last 3 items in dropq results list
            # get dict of results
            dq_fisc = dq_res[i - 3]
            for key in dq_fisc:
                if key.startswith("payroll_tax"):
                    res_fisc[i]["payroll_tax"].append(dq_fisc[key])
                elif key.startswith("combined_tax"):
                    res_fisc[i]["combined_tax"].append(dq_fisc[key])
                else:
                    assert key.startswith("ind_tax")
                    res_fisc[i]["ind_tax"].append(dq_fisc[key])

    # add fiscal_* results to main results dictionary
    for i in range(len(res_fisc_names)):
        results[res_fisc_names[i]] = res_fisc[i]

    return results


# following numpy.testing.assert_equal
# needed to adjust tolerances but numpy.testing.assert_equal does
# not do that
MSG = "\n\tNOT EQUAL: \n\t\t TB: {tb} \n\n\t\t DQ: {dq} \n\n\t\t keys: {k}"
def assert_results_equal(tb, dq, keys=[]):
    if isinstance(tb, dict) and isinstance(dq, dict):
        try:
            assert len(tb) == len(dq)
        except AssertionError:
            raise AssertionError(MSG.format(tb=tb, dq=dq, k=keys))
        for k in tb.keys():
            try:
                assert k in dq
            except AssertionError:
                raise AssertionError(MSG.format(tb=tb, dq=dq, k=keys))
            assert_results_equal(tb[k], dq[k], keys=keys + [k])
    elif isinstance(tb, list) and isinstance(dq, list):
        try:
            assert len(tb) == len(dq)
        except AssertionError:
            raise AssertionError(MSG.format(tb=tb, dq=dq, k=keys))
        for k in range(len(tb)):
            assert_results_equal(tb[k], dq[k], keys=keys + [k])
    else:
        try:
            if tb != dq:
                try:
                    tb = float(tb)
                    dq = float(dq)
                    assert np.allclose(tb, dq, rtol=0.02, atol=0.0)
                except ValueError:
                    assert tb == dq
        except AssertionError:
            raise AssertionError(MSG.format(tb=tb, dq=dq, k=keys))
