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


def run_micro_macro(reform, user_params, guid):

    start_time = time.time()

    REFORM_DIR = "./OUTPUT_REFORM_" + guid
    BASELINE_DIR = "./OUTPUT_BASELINE_" + guid

    # Add start year from reform to user parameters
    if isinstance(reform, tuple):
        start_year = sorted(reform[0].keys())[0]
    else:
        start_year = sorted(reform.keys())[0]
    user_params['start_year'] = start_year

    with open("log_{}.log".format(guid), 'w') as f:
        f.write("guid: {}\n".format(guid))
        f.write("reform: {}\n".format(reform))
        f.write("user_params: {}\n".format(user_params))

    '''
    ------------------------------------------------------------------------
        Run baseline
    ------------------------------------------------------------------------
    '''
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
    2017: {
        '_II_rt1': [.09],
        '_II_rt2': [.135],
        '_II_rt3': [.225],
        '_II_rt4': [.252],
        '_II_rt5': [.297],
        '_II_rt6': [.315],
        '_II_rt7': [0.3564],
    }, }
    run_micro_macro(reform=reform, user_params={'frisch': 0.44}, guid='abc')
