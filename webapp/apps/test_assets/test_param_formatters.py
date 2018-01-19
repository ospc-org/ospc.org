import json
import pytest
import taxcalc
import numpy as np
from collections import defaultdict

from ..taxbrain.views import (read_json_reform, parse_errors_warnings,
                              append_errors_warnings)

from ..taxbrain.helpers import (get_default_policy_param_name, to_json_reform)

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
    ("_fields,_exp_reform"),
    [("test_coverage_fields", "test_coverage_reform"),
     ("errors_warnings_fields", "errors_warnings_reform")]
)
def test_to_json_reform(request, _fields, _exp_reform):
    fields = request.getfixturevalue(_fields)
    exp_reform = request.getfixturevalue(_exp_reform)
    act, _ = to_json_reform(fields, START_YEAR)
    np.testing.assert_equal(act, exp_reform)

###############################################################################
# Test parse_errors_warnings
def test_parse_errors_warnings(errors_warnings, map_back_to_tb,
                               exp_errors_warnings):
    act = parse_errors_warnings(errors_warnings, map_back_to_tb)
    np.testing.assert_equal(act, exp_errors_warnings)


def test_append_ew_file_input():
    """
    Tests append_errors_warnings when add warning/error messages from the
    file input interface
    """
    errors_warnings = {"warnings": {"param1": {"2017": "msg2", "2016": "msg1"}},
                       "errors": {"param2": {"2018": "msg3", "2019": "msg4"}}
                       }
    errors = []
    exp = ["msg1", "msg2", "msg3", "msg4"]

    append_errors_warnings(
        errors_warnings,
        lambda _, msg: errors.append(msg)
    )

    assert errors == exp

def test_append_ew_personal_inputs():
    """
    Tests append_errors_warnings when adding warning/error messages from the
    GUI input interface
    """
    errors_warnings = {"warnings": {"param1": {"2017": "msg2", "2016": "msg1"}},
                       "errors": {"param2": {"2018": "msg3", "2019": "msg4"}}
                       }
    # fake PersonalExemptionForm object to simulate add_error method
    class FakeForm:
        def __init__(self):
            self.errors = defaultdict(list)

        def add_error(self, param_name, msg):
            self.errors[param_name].append(msg)

    exp = {"param1": ["msg1", "msg2"],
           "param2": ["msg3", "msg4"]}

    personal_inputs = FakeForm()
    append_errors_warnings(
        errors_warnings,
        lambda param, msg: personal_inputs.add_error(param, msg)
    )

    assert (exp["param1"] == personal_inputs.errors["param1"] and
            exp["param2"] == personal_inputs.errors["param2"])


###############################################################################
# Test read_json_reform
# 3 Cases:
#   1. Reform does not throw errors and no behavior assumptions are made
#   2. Reform does not throw errors and behavior assumptions are made
#   3. Reform throws errors and warnings and behavior assumptions are not made
@pytest.mark.parametrize(
    ("_test_reform,_test_assump,_map_back_to_tb,_exp_reform,_exp_assump,"
     "_exp_errors_warnings"),
    [("test_coverage_json_reform", "no_assumptions_text",
      "map_back_to_tb", "test_coverage_exp_read_json_reform",
      "no_assumptions_text_json",
      "empty_errors_warnings"),
     ("test_coverage_json_reform", "assumptions_text",
      "map_back_to_tb", "test_coverage_exp_read_json_reform",
      "exp_assumptions_text",
      "empty_errors_warnings"),
     ("errors_warnings_json_reform", "no_assumptions_text",
      "map_back_to_tb", "errors_warnings_exp_read_json_reform",
      "no_assumptions_text_json", "exp_errors_warnings")
     ]
)
def test_read_json_reform(request, _test_reform, _test_assump, _map_back_to_tb,
                          _exp_reform, _exp_assump, _exp_errors_warnings):
    test_reform = request.getfixturevalue(_test_reform)
    test_assump = request.getfixturevalue(_test_assump)
    map_back_to_tb = request.getfixturevalue(_map_back_to_tb)
    exp_reform = request.getfixturevalue(_exp_reform)
    exp_assump = request.getfixturevalue(_exp_assump)
    exp_errors_warnings = request.getfixturevalue(_exp_errors_warnings)


    act_reform, act_assump, act_errors_warnings = read_json_reform(
        test_reform,
        test_assump,
        map_back_to_tb
    )
    np.testing.assert_equal(act_reform, exp_reform)
    np.testing.assert_equal(act_assump, exp_assump)
    np.testing.assert_equal(act_errors_warnings, exp_errors_warnings)
