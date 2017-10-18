import json
import pytest
import taxcalc
import numpy as np

from ..taxbrain.views import (parse_errors_warnings, read_json_reform,
                              get_reform_from_gui, get_reform_from_file)
from ..taxbrain.helpers import (get_default_policy_param_name, to_json_reform)

from test_reform import (test_coverage_fields, test_coverage_reform,
                         test_coverage_json_reform,
                         test_coverage_json_assumptions,
                         test_coverage_map_back_to_tb,
                         test_coverage_exp_read_json_reform)

from test_assumptions import assumptions_text

START_YEAR = 2017

@pytest.fixture
def default_params_Policy():
    return taxcalc.Policy.default_data(start_year=START_YEAR,
                                       metadata=True)


###############################################################################
# Test get_default_policy_param_name
@pytest.mark.parametrize("param,exp_param",
                         [("FICA_ss_trt", "_FICA_ss_trt"),
                          ("ID_BenefitSurtax_Switch_0", "_ID_BenefitSurtax_Switch_medical"),
                          ("CG_brk3_cpi", "_CG_brk3_cpi")])
def test_get_default_policy_param_name_passing(param, exp_param, default_params_Policy):
    act_param = get_default_policy_param_name(param, default_params_Policy)
    assert act_param == exp_param

@pytest.mark.parametrize("param", ["CG_brk3_extra_cpi", "not_a_param"])
def test_get_default_policy_param_name_failing0(param, default_params_Policy):
    match="Received unexpected parameter: {0}".format(param)
    with pytest.raises(ValueError, match=match):
        get_default_policy_param_name(param, default_params_Policy)


def test_get_default_policy_param_name_failing1(default_params_Policy):
    param = "ID_BenefitSurtax_Switch_idx"
    match="Parsing {0}: Index {0} not in range".format(param, "idx")
    with pytest.raises(ValueError, match=match):
        get_default_policy_param_name(param, default_params_Policy)


def test_get_default_policy_param_name_failing2(default_params_Policy):
    param = "ID_BenefitSurtax_Switch_12"
    match="Parsing {}: Expected integer for index but got {}".format(param, "12")
    with pytest.raises(ValueError, match=match):
        get_default_policy_param_name(param, default_params_Policy)

###############################################################################
# Test to_json_reform

def test_to_json_reform():
    act, _ = to_json_reform(test_coverage_fields, START_YEAR)
    np.testing.assert_equal(act, test_coverage_reform)

###############################################################################
# Test parse_errors_warnings
REFORM_WARNINGS_ERRORS = {
    u'policy': {
        u'_STD_single': {u'2017': [7000.0]},
        u'_FICA_ss_trt': {u'2017': [-1.0], u'2019': [0.1]},
        u'_II_brk4_single': {u'2017': [500.0]},
        u'_STD_headhousehold': {u'2017': [10000.0], u'2020': [150.0]},
        u'_ID_BenefitSurtax_Switch_medical': {u'2017': [True]}
    }
}

ERRORS = ("ERROR: 2017 _FICA_ss_trt value -1.0 < min value 0\n"
          "ERROR: 2018 _FICA_ss_trt value -1.0 < min value 0\n"
          "ERROR: 2017 _II_brk4_0 value 500.0 < min value 91900.0 for _II_brk3_0\n"
          "ERROR: 2018 _II_brk4_0 value 511.1 < min value 93940.18 for _II_brk3_0\n"
          "ERROR: 2019 _II_brk4_0 value 522.8 < min value 96091.41 for _II_brk3_0\n"
          "ERROR: 2020 _II_brk4_0 value 534.98 < min value 98330.34 for _II_brk3_0\n"
          "ERROR: 2021 _II_brk4_0 value 547.45 < min value 100621.44 for _II_brk3_0\n"
          "ERROR: 2022 _II_brk4_0 value 560.15 < min value 102955.86 for _II_brk3_0\n"
          "ERROR: 2023 _II_brk4_0 value 573.2 < min value 105354.73 for _II_brk3_0\n"
          "ERROR: 2024 _II_brk4_0 value 586.56 < min value 107809.5 for _II_brk3_0\n"
          "ERROR: 2025 _II_brk4_0 value 600.29 < min value 110332.24 for _II_brk3_0\n"
          "ERROR: 2026 _II_brk4_0 value 614.4 < min value 112925.05 for _II_brk3_0\n")

WARNINGS = ("WARNING: 2020 _STD_3 value 150.0 < min value 10004.23\n"
            "WARNING: 2021 _STD_3 value 153.5 < min value 10237.33\n"
            "WARNING: 2022 _STD_3 value 157.06 < min value 10474.84\n"
            "WARNING: 2023 _STD_3 value 160.72 < min value 10718.9\n"
            "WARNING: 2024 _STD_3 value 164.46 < min value 10968.65\n"
            "WARNING: 2025 _STD_3 value 168.31 < min value 11225.32\n"
            "WARNING: 2026 _STD_3 value 172.27 < min value 11489.12\n")

ERRORS_WARNINGS = {'errors': ERRORS, 'warnings': WARNINGS}

EXP_ERRORS_WARNINGS = {
    'errors': {
        '2024': {'II_brk4_0': 'ERROR: value 586.56 < min value 107809.5 for _II_brk3_0 for 2024'},
        '2025': {'II_brk4_0': 'ERROR: value 600.29 < min value 110332.24 for _II_brk3_0 for 2025'},
        '2026': {'II_brk4_0': 'ERROR: value 614.4 < min value 112925.05 for _II_brk3_0 for 2026'},
        '2020': {'II_brk4_0': 'ERROR: value 534.98 < min value 98330.34 for _II_brk3_0 for 2020'},
        '2018': {'FICA_ss_trt': 'ERROR: value -1.0 < min value 0 for 2018',
                 'II_brk4_0': 'ERROR: value 511.1 < min value 93940.18 for _II_brk3_0 for 2018'},
        '2022': {'II_brk4_0': 'ERROR: value 560.15 < min value 102955.86 for _II_brk3_0 for 2022'},
        '2023': {'II_brk4_0': 'ERROR: value 573.2 < min value 105354.73 for _II_brk3_0 for 2023'},
        '2019': {'II_brk4_0': 'ERROR: value 522.8 < min value 96091.41 for _II_brk3_0 for 2019'},
        '2017': {'FICA_ss_trt': 'ERROR: value -1.0 < min value 0 for 2017',
                 'II_brk4_0': 'ERROR: value 500.0 < min value 91900.0 for _II_brk3_0 for 2017'},
        '2021': {'II_brk4_0': 'ERROR: value 547.45 < min value 100621.44 for _II_brk3_0 for 2021'}
        },
    'warnings': {
        '2024': {'STD_3': 'WARNING: value 164.46 < min value 10968.65 for 2024'},
        '2025': {'STD_3': 'WARNING: value 168.31 < min value 11225.32 for 2025'},
        '2026': {'STD_3': 'WARNING: value 172.27 < min value 11489.12 for 2026'},
        '2020': {'STD_3': 'WARNING: value 150.0 < min value 10004.23 for 2020'},
        '2021': {'STD_3': 'WARNING: value 153.5 < min value 10237.33 for 2021'},
        '2022': {'STD_3': 'WARNING: value 157.06 < min value 10474.84 for 2022'},
        '2023': {'STD_3': 'WARNING: value 160.72 < min value 10718.9 for 2023'}
    }
}

MAP_BACK_TO_TB = {
    u'_STD_single': 'STD_0',
    '_FICA_ss_trt': 'FICA_ss_trt',
    u'_STD_headhousehold': 'STD_3',
    u'_II_brk4_single': 'II_brk4_0',
    u'_ID_BenefitSurtax_Switch_medical': 'ID_BenefitSurtax_Switch_0'
}

def test_parse_errors_warnings():
    act = parse_errors_warnings(ERRORS_WARNINGS, MAP_BACK_TO_TB)
    np.testing.assert_equal(EXP_ERRORS_WARNINGS, act)


###############################################################################
# Test read_json_reform
@pytest.mark.parametrize(
    ("test_reform,test_assump,map_back_to_tb,exp_reform,exp_assump,"
     "exp_errors_warnings"),
    [(test_coverage_json_reform, test_coverage_json_assumptions,
      test_coverage_map_back_to_tb, test_coverage_exp_read_json_reform,
      json.loads(test_coverage_json_assumptions),
      {'errors': {}, 'warnings': {}}),
      (test_coverage_json_reform, assumptions_text,
        test_coverage_map_back_to_tb, test_coverage_exp_read_json_reform,
        json.loads(assumptions_text),
        {'errors': {}, 'warnings': {}}),
     (REFORM_WARNINGS_ERRORS, test_coverage_json_assumptions, MAP_BACK_TO_TB,
      False, json.loads(test_coverage_json_assumptions), ERRORS_WARNINGS)
     ]
)
def test_read_json_reform(test_reform, test_assump, map_back_to_tb,
                          exp_reform, exp_assump, exp_errors_warnings):
    exp_assump = json.loads(test_coverage_json_assumptions)
    exp_errors_warnings = {'errors': {}, 'warnings': {}}

    act_reform, act_assump, act_errors_warnings = read_json_reform(
        test_coverage_json_reform,
        test_coverage_json_assumptions,
        test_coverage_map_back_to_tb
    )

    np.testing.assert_equal(test_coverage_exp_read_json_reform, act_reform)
    np.testing.assert_equal(exp_assump, act_assump)
    np.testing.assert_equal(exp_errors_warnings, act_errors_warnings)
