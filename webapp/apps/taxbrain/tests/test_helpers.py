import pytest
import json
import taxcalc
from ..helpers import nested_form_parameters

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
    assert (len(res) == 2 and "ALD_EarlyWithdraw_hc" in res
            and "ALD_IRAContributions_hc" in res)

    params = nested_form_parameters(2017, use_puf_not_cps=False,
                                    defaults=mock_current_law_policy)
    res = params[0]['Above The Line Deductions'][0]['Misc. Adjustment Haircuts']
    res = {k: v for r in res for k, v in r.iteritems()}
    assert (len(res) == 1 and "ALD_EarlyWithdraw_hc" not in res
            and "ALD_IRAContributions_hc" in res)
