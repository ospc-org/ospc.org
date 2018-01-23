import os
import sys
import uuid
from multiprocessing import Process
import time

OGUSA_PATH = os.environ.get("OGUSA_PATH", "../../ospc-dynamic/dynamic/Python")

sys.path.append(OGUSA_PATH)

import ogusa
from ogusa.scripts import postprocess
from ogusa.scripts.execute import runner


def run_micro_macro(start_year, reform, user_params, guid):

    start_time = time.time()

    REFORM_DIR = "./OUTPUT_REFORM_" + guid
    BASELINE_DIR = "./OUTPUT_BASELINE_" + guid

    with open("log_{}.log".format(guid), 'w') as f:
        f.write("guid: {}\n".format(guid))
        f.write("reform: {}\n".format(reform))
        f.write("user_params: {}\n".format(user_params))

    '''
    ------------------------------------------------------------------------
        Run baseline
    ------------------------------------------------------------------------
    '''

    user_params["start_year"] = start_year
    output_base = BASELINE_DIR
    kwargs={'output_base':output_base, 'baseline_dir':BASELINE_DIR,
            'test':False, 'time_path':True, 'baseline':True,
            'analytical_mtrs':False, 'age_specific':False,
            'user_params':user_params,'guid':guid,
            'run_micro':True, 'small_open': False, 'budget_balance':False, 'baseline_spending':False}
    #p2 = Process(target=runner, kwargs=kwargs)
    #p2.start()
    runner(**kwargs)

    '''
    ------------------------------------------------------------------------
        Run reform
    ------------------------------------------------------------------------
    '''

    output_base = REFORM_DIR
    kwargs={'output_base':output_base, 'baseline_dir':BASELINE_DIR,
            'test':False, 'time_path':True, 'baseline':False,
            'analytical_mtrs':False, 'age_specific':False,
            'user_params':user_params,'guid':guid,
            'run_micro':True, 'small_open': False, 'budget_balance':False, 'baseline_spending':False}
    #p1 = Process(target=runner, kwargs=kwargs)
    #p1.start()
    runner(**kwargs)

    #p1.join()
    #p2.join()

    time.sleep(0.5)
    ans = postprocess.create_diff(baseline_dir=BASELINE_DIR, policy_dir=REFORM_DIR)
    print "total time was ", (time.time() - start_time)

    return ans

if __name__ == "__main__":

    reform = {
        u'growdiff_response': {},
        u'consumption': {},
        u'growdiff_baseline': {},
        u'behavior': {},
        u'policy': {
            2017: {
                u'_II_no_em_nu18': [False],
                u'_NIIT_PT_taxed': [False],
                u'_FICA_ss_trt': [0.1],
                u'_ID_BenefitCap_Switch': [[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]],
                u'_ALD_InvInc_ec_base_RyanBrady': [False],
                u'_EITC_indiv': [False],
                u'_ID_BenefitSurtax_Switch': [[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]],
                u'_CTC_new_refund_limited': [False],
                u'_CG_nodiff': [False]
            }
        },
        u'gdp_elasticity': {}
    }
    user_params = {u'g_y_annual': 0.04, u'frisch': 0.3}

    run_micro_macro(start_year=2017, reform=reform, user_params=user_params, guid='abc')
