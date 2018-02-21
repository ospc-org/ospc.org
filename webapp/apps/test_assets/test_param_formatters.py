import json
import os
import pytest
import taxcalc
import numpy as np
from collections import defaultdict, OrderedDict

from ..taxbrain.param_formatters import (read_json_reform,
                                         parse_errors_warnings,
                                         append_errors_warnings,
                                         get_default_policy_param,
                                         to_json_reform, MetaParam,
                                         parse_value, parse_fields,
                                         ParameterLookUpException)

from .utils import stringify_fields

START_YEAR = 2017
CUR_PATH = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def default_params_Policy():
    return taxcalc.Policy.default_data(start_year=START_YEAR,
                                       metadata=True)


###############################################################################
# Test get_default_policy_param
# 3 Cases for search success:
#   1. "_" + param name
#   2. "_" + param name + index name (i.e. STD_0 --> _STD_single)
#   3. "_" + param name minus "_cpi"
@pytest.mark.parametrize("param,exp_param",
                         [("FICA_ss_trt", "_FICA_ss_trt"),
                          ("ID_BenefitSurtax_Switch_0", "_ID_BenefitSurtax_Switch_medical"),
                          ("CG_brk3_cpi", "_CG_brk3_cpi")])
def test_get_default_policy_param_passing(param, exp_param, default_params_Policy):
    act_param = get_default_policy_param(param, default_params_Policy)
    assert isinstance(act_param, MetaParam)
    np.testing.assert_equal(act_param.param_name, exp_param)
    assert isinstance(act_param.param_meta, (dict, OrderedDict))

@pytest.mark.parametrize("param", ["CG_brk3_extra_cpi", "not_a_param"])
def test_get_default_policy_param_failing0(param, default_params_Policy):
    """
    Check that non-recognized parameters throw a ValueError
    """
    match="Received unexpected parameter: {0}".format(param)
    with pytest.raises(ParameterLookUpException, match=match):
        get_default_policy_param(param, default_params_Policy)


def test_get_default_policy_param_failing1(default_params_Policy):
    """
    Check that parameter with non-integer characters after the final '_'
    throws ValueError
    """
    param = "ID_BenefitSurtax_Switch_idx"
    match = "Parsing {}: Expected integer for index but got {}".format(param, "idx")
    with pytest.raises(ParameterLookUpException, match=match):
        get_default_policy_param(param, default_params_Policy)


def test_get_default_policy_param_failing2(default_params_Policy):
    """
    Check that parameter with correct name but out of bounds index throws
    IndexError
    """
    param = "ID_BenefitSurtax_Switch_12"
    # comment out "(" since this is treated as a regexp string
    match = "Parsing {}: Index {} not in range \({}, {}\)"
    match = match.format(param, 12, 0, 7)
    with pytest.raises(ParameterLookUpException, match=match):
        get_default_policy_param(param, default_params_Policy)

##############################################################################
# Test meta_apram construction and attribute access
def test_meta_param():
    name_part = 'param_name'
    dict_part = {'dict': 'has some meta info'}
    meta_param = MetaParam(name_part, dict_part)
    assert meta_param.param_name == name_part
    assert meta_param.param_meta == dict_part

##############################################################################
# Test parse_value
@pytest.mark.parametrize(
    "name,value,exp",
    [("FICA_ss_trt", "0.10", 0.10), ("ID_BenefitCap_Switch_0", "True", True),
     ("EITC_MinEligAge", "22", 22), ("EITC_indiv", "True", True),
     ("AMEDT_ec_0", "300000", 300000.0),
     ("ID_BenefitCap_Switch_0", "0", False), ("STD_1", "<", "<"),
     ("STD_2", "*", "*"), ("EITC_MinEligAge", "22.2", 22.2),
     ("EITC_MinEligAge", "22.0", 22),
     ("ID_BenefitCap_Switch_0", "fAlse", False),
     ("ID_Medical_frt_add4aged", "-0.01", -0.01),
     ("ID_Charity_c_cpi", "True", True), ("ID_Medical_c_cpi", "1", True)
    ]
)
def test_parse_values(name, value, exp, default_params_Policy):
    meta_param = get_default_policy_param(name, default_params_Policy)
    assert parse_value(value, meta_param) == exp

# Test meta_param construction and attribute access
def test_parse_fields(default_params_Policy):
    params = {"FICA_ss_trt": "<,0.10", "ID_BenefitCap_Switch_0": "True,*,False",
              "EITC_MinEligAge": "22",
              "AMEDT_ec_0": "300000,*,250000.0",
              "STD_0": "", "STD_1": "15000,<",
              "ID_BenefitCap_Switch_1": "True,fALse,<,TRUE, true",
              "ID_Charity_c_cpi": "True",
              "ID_Medical_c_cpi": "1",
              "not-a-param": "fake"}
    act, failed_lookups = parse_fields(params, default_params_Policy)
    exp = {
        '_AMEDT_ec_single': [300000.0, '*', 250000.0],
        '_EITC_MinEligAge': [22],
        '_FICA_ss_trt': ['<', 0.1],
        '_ID_BenefitCap_Switch_medical': [True, '*', False],
        "_STD_joint": [15000.0,"<"],
        "_ID_BenefitCap_Switch_statelocal": [True, False, "<", True, True],
        "_ID_Charity_c_cpi": True,
        "_ID_Medical_c_cpi": True
    }
    assert act == exp
    assert failed_lookups == ["not-a-param"]

###############################################################################
# Test to_json_reform
# 2 Cases:
#   1. Fields do not cause errors
#   2. Fields cause errors
@pytest.mark.parametrize(
    ("_fields,_exp_reform"),
    [("test_coverage_gui_fields", "test_coverage_reform"),
     ("errors_warnings_gui_fields", "errors_warnings_reform")]
)
def test_to_json_reform(request, _fields, _exp_reform, default_params_Policy):
    fields = request.getfixturevalue(_fields)
    stringified_fields = stringify_fields(fields)
    parsed_fields, _ = parse_fields(stringified_fields, default_params_Policy)
    exp_reform = request.getfixturevalue(_exp_reform)
    act = to_json_reform(START_YEAR, parsed_fields)
    np.testing.assert_equal(act, exp_reform)

###############################################################################
# Test parse_errors_warnings
def test_parse_errors_warnings(errors_warnings,
                               exp_errors_warnings):
    act = parse_errors_warnings(errors_warnings)
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
    ("_test_reform,_test_assump,_exp_reform,_exp_assump,"
     "_exp_errors_warnings"),
    [("test_coverage_json_reform", "no_assumptions_text",
      "test_coverage_exp_read_json_reform",
      "no_assumptions_text_json",
      "empty_errors_warnings"),
     ("test_coverage_json_reform", "assumptions_text",
      "test_coverage_exp_read_json_reform",
      "exp_assumptions_text",
      "empty_errors_warnings"),
     ("errors_warnings_json_reform", "no_assumptions_text",
      "errors_warnings_exp_read_json_reform",
      "no_assumptions_text_json", "exp_errors_warnings")
     ]
)
def test_read_json_reform(request, _test_reform, _test_assump,
                          _exp_reform, _exp_assump, _exp_errors_warnings):
    test_reform = request.getfixturevalue(_test_reform)
    test_assump = request.getfixturevalue(_test_assump)
    exp_reform = request.getfixturevalue(_exp_reform)
    exp_assump = request.getfixturevalue(_exp_assump)
    exp_errors_warnings = request.getfixturevalue(_exp_errors_warnings)


    act_reform, act_assump, act_errors_warnings = read_json_reform(
        test_reform,
        test_assump
    )
    np.testing.assert_equal(act_reform, exp_reform)
    np.testing.assert_equal(act_assump, exp_assump)
    np.testing.assert_equal(act_errors_warnings, exp_errors_warnings)


###############################################################################
# Update test data
#
# def test_update_errors_warnings(errors_warnings_json_reform, map_back_to_tb):
#     import taxcalc
#     policy_dict = taxcalc.Calculator.read_json_param_objects(
#         errors_warnings_json_reform,
#         None
#     )
#     pol = taxcalc.Policy()
#     pol.implement_reform(policy_dict['policy'])
#     print('warnings', pol.reform_warnings)
#     print('errors', pol.reform_errors)
#
#
#     with open(os.path.join(CUR_PATH, 'warnings.txt'), 'w') as f:
#         f.write(pol.reform_warnings)
#     with open(os.path.join(CUR_PATH, 'errors.txt'), 'w') as f:
#         f.write(pol.reform_errors)
#
#     _errors_warnings = {'errors': pol.reform_errors,
#                         'warnings': pol.reform_warnings}
#
#     act = parse_errors_warnings(_errors_warnings, map_back_to_tb)
#     print('errors_warnings', act)
#
#     with open(os.path.join(CUR_PATH, 'exp_errors_warnings'), 'w') as f:
#         f.write(json.dumps(act, indent=4))
#
#
# def test_update_test_data_read_json_reform1(test_coverage_json_reform,
#                                             no_assumptions_text, map_back_to_tb,
#                                             test_coverage_exp_read_json_reform,
#                                             no_assumptions_text_json,
#                                             empty_errors_warnings):
#
#     act_reform, act_assump, act_errors_warnings = read_json_reform(
#         test_coverage_json_reform,
#         no_assumptions_text,
#         map_back_to_tb
#     )
#     print('act_reform', act_reform)
#     print('act_assump', act_assump)
#     print('act_errors_warnings', act_errors_warnings)
#
#
# def test_update_test_data_read_json_reform2(test_coverage_json_reform,
#                                             assumptions_text,
#                                             map_back_to_tb,
#                                             test_coverage_exp_read_json_reform,
#                                             exp_assumptions_text,
#                                             empty_errors_warnings):
#
#     act_reform, act_assump, act_errors_warnings = read_json_reform(
#         test_coverage_json_reform,
#         assumptions_text,
#         map_back_to_tb
#     )
#     print('act_reform', act_reform)
#     print('act_assump', act_assump)
#     print('act_errors_warnings', act_errors_warnings)
#
#
# def test_update_test_data_read_json_reform3(errors_warnings_json_reform,
#                                             no_assumptions_text,
#                                             map_back_to_tb,
#                                             errors_warnings_exp_read_json_reform,
#                                             no_assumptions_text_json,
#                                             exp_errors_warnings):
#
#     act_reform, act_assump, act_errors_warnings = read_json_reform(
#         errors_warnings_json_reform,
#         no_assumptions_text,
#         map_back_to_tb
#     )
#     print('act_reform', act_reform)
#     print('act_assump', act_assump)
#     print('act_errors_warnings', act_errors_warnings)
