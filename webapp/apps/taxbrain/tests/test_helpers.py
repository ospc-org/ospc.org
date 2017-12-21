import pytest
import json
import numpy as np
import taxcalc
import pyparsing as pp
from ..helpers import (nested_form_parameters, rename_keys, INPUT, make_bool,
                       TaxCalcParam)

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
    res = {k: v for r in res for k, v in r.iteritems()}
    assert (not res["ALD_EarlyWithdraw_hc"].gray_out and
            not res["ALD_IRAContributions_hc"].gray_out)

    params = nested_form_parameters(2017, use_puf_not_cps=False,
                                    defaults=mock_current_law_policy)
    res = params[0]['Above The Line Deductions'][0]['Misc. Adjustment Haircuts']
    res = {k: v for r in res for k, v in r.iteritems()}
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
     '1,*,False', '0.0,True', '1.0,False']
)
def test_parsing_pass(item):
    INPUT.parseString(item)

def test_parsing_fail():
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


def test_make_taxcalc_param():
    """
    Test creation of taxcalc param from comma separated boolean value
    """
    name =  u'_DependentCredit_before_CTC'
    attr = {
        u'integer_value': True,
        u'start_year': 2017,
        u'description': 'test',
        u'out_of_range_action': u'stop',
        u'col_var': u'',
        u'long_name': u'test',
        u'out_of_range_maxmsg': u'',
        u'row_var': u'FLPDYR',
        u'cpi_inflated': False,
        u'boolean_value': True,
        u'col_label': u'',
        u'out_of_range_minmsg': u'',
        u'notes': u'',
        u'value': [0],
        u'section_1': u'Nonrefundable Credits',
        u'irs_ref': u'',
        u'range': {u'min': False, u'max': True},
        u'section_2': u'Child Tax Credit',
        u'row_label': ['2017']
    }
    budget_year = 2017
    use_puf_not_cps = True

    param = TaxCalcParam(name, attr, budget_year, use_puf_not_cps)
    field = param.col_fields[0]
    assert field.values == ['False']

    attr['value'] = [0, 0, 1]
    param = TaxCalcParam(name, attr, budget_year, use_puf_not_cps)
    fields = param.col_fields
    for field, exp in zip(fields, ['False', 'False', 'True']):
        assert field.values == [exp]

    attr['value'] = [0, 0, 1]
    param = TaxCalcParam(name, attr, budget_year, use_puf_not_cps)
    fields = param.col_fields
    for field, exp in zip(fields, ['False', 'False', 'True']):
        assert field.values == [exp]

    attr['value'] = [[0, 0, 1]]
    param = TaxCalcParam(name, attr, budget_year, use_puf_not_cps)
    fields = param.col_fields
    for field, exp in zip(fields, ['False', 'False', 'True']):
        assert field.values == [exp]
