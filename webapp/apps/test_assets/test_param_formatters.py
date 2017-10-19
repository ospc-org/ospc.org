import json
import pytest
import taxcalc
import numpy as np

from ..taxbrain.views import read_json_reform, parse_errors_warnings
from ..taxbrain.helpers import (get_default_policy_param_name, to_json_reform)

from test_reform import (test_coverage_fields, test_coverage_reform,
                         test_coverage_json_reform,
                         test_coverage_exp_read_json_reform,
                         errors_warnings_fields, errors_warnings_reform,
                         errors_warnings_json_reform,
                         errors_warnings_exp_read_json_reform,
                         errors_warnings, exp_errors_warnings,
                         map_back_to_tb)

from test_assumptions import (assumptions_text, exp_assumptions_text, no_assumptions_text)

START_YEAR = 2017

@pytest.fixture
def default_params_Policy():
    return taxcalc.Policy.default_data(start_year=START_YEAR,
                                       metadata=True)


###############################################################################
# Test get_default_policy_param_name
# 3 Cases for search success:
#   1. "_" + param name
#   2. "_" + param name + index name (i.e. STD_0 --> _STD_single)
#   3. "_" + param name minus "_cpi"
@pytest.mark.parametrize("param,exp_param",
                         [("FICA_ss_trt", "_FICA_ss_trt"),
                          ("ID_BenefitSurtax_Switch_0", "_ID_BenefitSurtax_Switch_medical"),
                          ("CG_brk3_cpi", "_CG_brk3_cpi")])
def test_get_default_policy_param_name_passing(param, exp_param, default_params_Policy):
    act_param = get_default_policy_param_name(param, default_params_Policy)
    np.testing.assert_equal(act_param, exp_param)

@pytest.mark.parametrize("param", ["CG_brk3_extra_cpi", "not_a_param"])
def test_get_default_policy_param_name_failing0(param, default_params_Policy):
    """
    Check that non-recognized parameters throw a ValueError
    """
    match="Received unexpected parameter: {0}".format(param)
    with pytest.raises(ValueError, match=match):
        get_default_policy_param_name(param, default_params_Policy)


def test_get_default_policy_param_name_failing1(default_params_Policy):
    """
    Check that parameter with non-integer characters after the final '_'
    throws ValueError
    """
    param = "ID_BenefitSurtax_Switch_idx"
    match = "Parsing {}: Expected integer for index but got {}".format(param, "idx")
    with pytest.raises(ValueError, match=match):
        get_default_policy_param_name(param, default_params_Policy)


def test_get_default_policy_param_name_failing2(default_params_Policy):
    """
    Check that parameter with correct name but out of bounds index throws
    IndexError
    """
    param = "ID_BenefitSurtax_Switch_12"
    # comment out "(" since this is treated as a regexp string
    match = "Parsing {}: Index {} not in range \({}, {}\)"
    match = match.format(param, 12, 0, 7)
    with pytest.raises(IndexError, match=match):
        get_default_policy_param_name(param, default_params_Policy)

###############################################################################
# Test to_json_reform
# 2 Cases:
#   1. Fields do not cause errors
#   2. Fields cause errors
@pytest.mark.parametrize(
    ("fields,exp_reform"),
    [(test_coverage_fields, test_coverage_reform),
     (errors_warnings_fields, errors_warnings_reform)]
)
def test_to_json_reform(fields, exp_reform):
    act, _ = to_json_reform(fields, START_YEAR)
    np.testing.assert_equal(act, exp_reform)

###############################################################################
# Test parse_errors_warnings
def test_parse_errors_warnings():
    act = parse_errors_warnings(errors_warnings, map_back_to_tb)
    np.testing.assert_equal(exp_errors_warnings, act)


###############################################################################
# Test read_json_reform
# 3 Cases:
#   1. Reform does not throw errors and no behavior assumptions are made
#   2. Reform does not throw errors and behavior assumptions are made
#   3. Reform throws errors and warnings and behavior assumptions are not made
@pytest.mark.parametrize(
    ("test_reform,test_assump,map_back_to_tb,exp_reform,exp_assump,"
     "exp_errors_warnings"),
    [(test_coverage_json_reform, no_assumptions_text,
      map_back_to_tb, test_coverage_exp_read_json_reform,
      json.loads(no_assumptions_text),
      {'errors': {}, 'warnings': {}}),
     (test_coverage_json_reform, assumptions_text,
      map_back_to_tb, test_coverage_exp_read_json_reform,
      exp_assumptions_text,
      {'errors': {}, 'warnings': {}}),
     (errors_warnings_json_reform, no_assumptions_text,
      map_back_to_tb, errors_warnings_exp_read_json_reform,
      json.loads(no_assumptions_text), exp_errors_warnings)
     ]
)
def test_read_json_reform(test_reform, test_assump, map_back_to_tb,
                          exp_reform, exp_assump, exp_errors_warnings):
    act_reform, act_assump, act_errors_warnings = read_json_reform(
        test_reform,
        test_assump,
        map_back_to_tb
    )
    np.testing.assert_equal(exp_reform, act_reform)
    np.testing.assert_equal(exp_assump, act_assump)
    np.testing.assert_equal(exp_errors_warnings, act_errors_warnings)
