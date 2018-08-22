import pytest
import json
import taxcalc
from ..helpers import (json_int_key_encode, is_safe, make_bool,
                       is_reverse, convert_val)
from ..param_formatters import parse_value, MetaParam
from ..param_displayers import (TaxCalcParam, nested_form_parameters,
                                default_policy)


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
    res = (params[0]['Above The Line Deductions'][0]
                    ['Misc. Adjustment Haircuts'])
    res = {k: v for r in res for k, v in r.items()}
    assert (not res["ALD_EarlyWithdraw_hc"].gray_out and
            not res["ALD_IRAContributions_hc"].gray_out)

    params = nested_form_parameters(2017, use_puf_not_cps=False,
                                    defaults=mock_current_law_policy)
    res = (params[0]['Above The Line Deductions'][0]
                    ['Misc. Adjustment Haircuts'])
    res = {k: v for r in res for k, v in r.items()}
    assert (res["ALD_EarlyWithdraw_hc"].gray_out and
            not res["ALD_IRAContributions_hc"].gray_out)


def test_json_int_key_encode():
    exp = {2017: 'stuff', 2019: {2016: 'stuff', 2000: {1: 'heyo'}}}
    json_str = json.loads(json.dumps(exp))
    act = json_int_key_encode(json_str)
    assert exp == act


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
    assert is_safe(item)


@pytest.mark.parametrize('item', ['abc', '01', 'abc,def', '<,abc', '1,abc,2'])
def test_parsing_fail(item):
    assert not is_safe(item)


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


def test_convert_val():
    field = '*,*,130000'
    out = [convert_val(x) for x in field.split(',')]
    exp = ['*', '*', 130000.0]
    assert out == exp
    field = 'False'
    out = [convert_val(x) for x in field.split(',')]
    exp = [False]
    assert out == exp
    field = '0.12,0.13,0.14'
    out = [convert_val(x) for x in field.split(',')]
    exp = [0.12, 0.13, 0.14]
    assert out == exp


def test_default_taxcalc_data_cpi_flags_on_II_credit():
    taxcalc_default_params = default_policy(int(2017))
    assert taxcalc_default_params['II_credit'].inflatable
    assert taxcalc_default_params['II_credit_ps'].inflatable
