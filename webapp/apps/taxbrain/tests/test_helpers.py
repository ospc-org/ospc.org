import pytest
import json
import numpy as np
import taxcalc
import pyparsing as pp
from ..helpers import (rename_keys, json_int_key_encode, INPUT, make_bool,
                       is_reverse,
                       reorder_lists)
from ..param_formatters import parse_value, MetaParam
from ..param_displayers import TaxCalcParam, TaxCalcField, nested_form_parameters


CURRENT_LAW_POLICY = """
{
    "_ALD_IRAContributions_hc": {
        "long_name": "Deduction for IRA contributions haircut",
        "description": "If greater than zero, this decimal fraction reduces the portion of IRA contributions that can be deducted from AGI.",
        "section_1": "Above The Line Deductions",
        "section_2": "Misc. Adjustment Haircuts",
        "irs_ref": "",
        "notes": "The final adjustment amount would be (1-Haircut)*IRA_Contribution.",
        "row_var": "FLPDYR",
        "row_label": ["2013"],
        "start_year": 2013,
        "cpi_inflated": false,
        "col_var": "",
        "col_label": "",
        "boolean_value": false,
        "integer_value": false,
        "value": [0.0],
        "range": {"min": 0, "max": 1},
        "out_of_range_minmsg": "",
        "out_of_range_maxmsg": "",
        "out_of_range_action": "stop",
        "compatible_data": {"puf": true, "cps": true}
    },
    "_ALD_EarlyWithdraw_hc": {
            "long_name": "Adjustment for early withdrawal penalty haircut",
            "description": "Under current law, early withdraw penalty can be fully deducted from gross income. This haircut can be used to limit the adjustment allowed.",
            "section_1": "Above The Line Deductions",
            "section_2": "Misc. Adjustment Haircuts",
            "irs_ref": "Form 1040, line 30",
            "notes": "The final adjustment amount is (1-Haircut)*EarlyWithdrawPenalty.",
            "row_var": "FLPDYR",
            "row_label": ["2013"],
            "start_year": 2013,
            "cpi_inflated": false,
            "col_var": "",
            "col_label": "",
            "boolean_value": false,
            "integer_value": false,
            "value": [0.0],
            "range": {"min": 0, "max": 1},
            "out_of_range_minmsg": "",
            "out_of_range_maxmsg": "",
            "out_of_range_action": "stop",
            "compatible_data": {"puf": true, "cps": false}
    }
}
"""

@pytest.fixture
def mock_current_law_policy():
    return json.loads(CURRENT_LAW_POLICY)


def test_nested_form_parameters(monkeypatch, mock_current_law_policy):
    """
    Check that test_nested_form_parameters removes parameters that are not
    compatible with the specified data set
    """
    params = nested_form_parameters(2017, use_puf_not_cps=True,
                                    defaults=mock_current_law_policy)
    res = params[0]['Above The Line Deductions'][0]['Misc. Adjustment Haircuts']
    res = {k: v for r in res for k, v in r.items()}
    assert (not res["ALD_EarlyWithdraw_hc"].gray_out and
            not res["ALD_IRAContributions_hc"].gray_out)

    params = nested_form_parameters(2017, use_puf_not_cps=False,
                                    defaults=mock_current_law_policy)
    res = params[0]['Above The Line Deductions'][0]['Misc. Adjustment Haircuts']
    res = {k: v for r in res for k, v in r.items()}
    assert (res["ALD_EarlyWithdraw_hc"].gray_out and
            not res["ALD_IRAContributions_hc"].gray_out)


def test_rename_keys(monkeypatch):
    a = {
        'a': {
            'b': {
                'c': []
            }
        },
        'd': {
            'e': []
        },
        'f_1': [],
        'g': {
            'h': [],
            'i_0': [],
            'j': []
        }
    }
    exp = {
        'A': {
            'B': {
                'C': []
            }
        },
        'D': {
            'E': []
        },
        'F_1': [],
        'G': {
            'H': [],
            'I_0': [],
            'J': []
        }
    }

    map_dict = {
        'a': 'A',
        'b': 'B',
        'c': 'C',
        'd': 'D',
        'e': 'E',
        'f': 'F',
        'g': 'G',
        'h': 'H',
        'i': 'I',
        'j': 'J'
    }
    act = rename_keys(a, map_dict)
    np.testing.assert_equal(act, exp)


def test_json_int_key_encode():
    exp = {2017: 'stuff', 2019: {2016: 'stuff', 2000: {1: 'heyo'}}}
    json_str = json.loads(json.dumps(exp))
    act = json_int_key_encode(json_str)
    assert exp == act

def test_reorder_lists():
    reorder_map = [1, 0, 2]
    data = {"table_label_0": {"bin_0": [1, 0, 2], "bin_1": [1, 2, 0]},
            "table_label_1": {"bin_0": [1, 0, 2], "bin_1": [1, 2, 0]}}
    reorder_table_ids = ["table_label_0", "table_label_1"]

    res = reorder_lists(data, reorder_map, reorder_table_ids)

    assert (res["table_label_0"]["bin_0"] == [0, 1, 2])
    assert (res["table_label_0"]["bin_1"] == [2, 1, 0])
    assert (res["table_label_1"]["bin_0"] == [0, 1, 2])
    assert (res["table_label_1"]["bin_1"] == [2, 1, 0])


@pytest.mark.parametrize(
    'item',
    ['1', '2.0', '8.01', '23',
     '-4', '-3.0', '-2.02', '-46',
     '*', '1,*', '1,*,1,1,*',
     '-2,*', '-7,*,*,2,*',
     'True', 'true', 'TRUE', 'tRue',
     'False', 'false', 'FALSE','faLSe',
     'true,*', '*, true', '*,*,false',
     'true,*,false,*,*,true',
     '1,*,False', '0.0,True', '1.0,False',
     '<,True', '<,1']
)
def test_parsing_pass(item):
    INPUT.parseString(item)

@pytest.mark.parametrize('item', ['abc', '<,', '<', '1,<', '0,<,1', 'True,<', '-0.002,<,-0.001'])
def test_parsing_fail(item):
    with pytest.raises(pp.ParseException):
        INPUT.parseString('abc')

@pytest.mark.parametrize(
    'item,exp',
    [('True', True), ('true', True), ('TRUE', True), (True, True),
     ('tRue', True), (1.0, True), (1, True), ('1.0', True), ('1', True),
     ('False', False), ('false', False), ('FALSE', False), (False, False),
     ('faLSe', False), (0.0, False), (0, False), ('0.0', False), ('0', False)]
)
def test_make_bool(item, exp):
    assert make_bool(item) is exp

@pytest.mark.parametrize(
    'item',
    ['abc', 10, '10', '00', 2]
)
def test_make_bool_fail(item):
    with pytest.raises((ValueError, TypeError)):
        make_bool(item)

@pytest.mark.parametrize(
    'item,exp',
    [('<', True), ('a', False), ('1', False), (1, False), (False, False)])
def test_is_reverse(item, exp):
    assert is_reverse(item) is exp

def test_taxbrain_TaxCalcParam():
    """
    Test creation of TaxCalcParam objects.

    Strategy: treat the result from `parse_value` as the truth and test
    to make sure that the values are set correctly for display to
    the user.
    """
    dd = taxcalc.Policy.default_data(metadata=True, start_year=2017)

    for param_name in dd:
        tc_param = TaxCalcParam(param_name, dd[param_name], 2017)
        meta_param = MetaParam(
            param_name=param_name,
            param_meta=dd[param_name]
        )
        for field in tc_param.col_fields:
            for value in field.values_by_year:
                assert value == parse_value(str(value), meta_param)
