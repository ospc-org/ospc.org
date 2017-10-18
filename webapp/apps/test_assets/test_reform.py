reform_text = """// Title: 2016 Trump Campaign Tax Plan
// Reform_File_Author: Matt Jensen
// Reform_Reference: https://www.donaldjtrump.com/policies/tax-plan
// Reform_Description:
// -  New personal income tax schedule (regular/non-AMT/non-pass-through) (1)
// -  New pass-through income tax schedule (2)
// -  New long-term capital gains and qualified dividends tax schedule (3)
// -  Repeal Alternative Minimum Tax (4)
// -  Repeal Net Investment Income Tax (5)
// -  Raise the Standard Deduction (6)
// -  Repeal the Personal Exemption (7)
// -  New above the line deduction for child and elder care (8)
// -  Cap itemized deductions (9)
// Reform_Parameter_Map:
// - 1: _II_rt*, II_brk*
// - 2: _PT_*
// - 3: _CG_*
// - 4: _AMT_*
// - 5: _NIIT_rt
// - 6: _STD
// - 7: _II_em
// - 8: _ALD_Dependents*
// - 9: _ID_c
{
    "policy": {
        "_II_rt1": {
            "2017": [0.12],
            "2018": [0.12]
        },
        "_II_brk1":
            {"2017": [[37500, 75000, 37500, 37500, 75000]]},
        "_II_rt2":
            {"2017": [0.25]},
        "_II_brk2":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_II_rt3":
            {"2017":  [0.25]},
        "_II_brk3":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_II_rt4":
            {"2017":  [0.25]},
        "_II_brk4":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_II_rt5":
            {"2017": [0.25]},
        "_II_brk5":
            {"2017":  [[112500, 225000, 112500, 112500, 225000]]},
        "_II_rt6":
            {"2017": [0.25]},
        "_II_brk6":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_II_rt7":
            {"2017": [0.33]},
        "_PT_rt1":
            {"2017": [0.12]},
        "_PT_brk1":
            {"2017": [[37500, 75000, 37500, 37500, 75000]]},
        "_PT_rt2":
            {"2017": [0.15]},
        "_PT_brk2":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_PT_rt3":
            {"2017": [0.15]},
        "_PT_brk3":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_PT_rt4":
            {"2017": [0.15]},
        "_PT_brk4":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_PT_rt5":
            {"2017": [0.15]},
        "_PT_brk5":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_PT_rt6":
            {"2017": [0.15]},
        "_PT_brk6":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_PT_rt7":
            {"2017": [0.15]},
        "_CG_brk1":
            {"2017": [[37500, 75000, 37500, 37500, 75000]]},
        "_CG_brk2":
            {"2017": [[112500, 225000, 112500, 112500, 225000]]},
        "_AMT_rt1":
            {"2017": [0]},
        "_AMT_rt2":
            {"2017": [0]},
        "_NIIT_rt":
            {"2017": [0]},
        "_STD":
            {"2017": [[15000, 30000, 15000, 15000, 30000]]},
        "_II_em":
            {"2017": [0]},
        "_ALD_Dependents_thd":
            {"2017": [[250000, 500000, 250000, 500000, 500000]]},
        "_ALD_Dependents_Elder_c":
            {"2017": [5000]},
        "_ALD_Dependents_Child_c":
            {"2017": [7156]},
        "_ID_c":
            {"2017": [[100000, 200000, 100000, 100000, 200000]]}
    }
}

// Note: Due to lack of detail, data, or modeling capability, many provisions cannot be scored.
// These omitted provisions include:
// -  Allow expenssing for pass-through firms
// -  Tax carried interest as ordinary business income
// -  Repeal pass-through business tax expenditures
// -  Corporate tax provisions
// -  Estate tax provisions"""

regression_sample_reform = """// Assume reform with the following provisions:
// - adhoc raises in OASDI maximum taxable earnings in 2018, 2019 and 2020,
//     with _SS_Earnings_c wage indexed in subsequent years
// - raise personal exemption amount _II_em in 2018, keep it unchanged for
//     two years and then resume its price indexing in subsequent years
// - implement a 20% investment income AGI exclusion beginning in 2019
{
    "policy": {
        "_SS_Earnings_c": {"2018": [400000],
                           "2019": [500000],
                           "2020": [600000]},
        "_II_em": {"2018": [8000]},
        "_II_em_cpi": {"2018": false,
                       "2020": true},
        "_ALD_InvInc_ec_rt": {"2019": [0.20]}
    }
}"""

bad_reform = """// bad-reform.json contains a logically incorrect attempt to completely
// eliminate the income tax (leaving refundable credits unchanged)
{
    "policy": {
        "_II_rt1": {"2020": [0.0]},
        "_II_brk1": {"2020": [[9e99, 9e99, 9e99, 9e99, 9e99]]},
        "_CG_rt1": {"2020": [0.0]},
        "_CG_rt2": {"2020": [0.0]},
        "_CG_rt3": {"2020": [0.0]},
        "_CG_rt4": {"2020": [0.0]},
        "_AMT_rt1": {"2020": [0.0]},
        "_AMT_rt2": {"2020": [0.0]},
        "_AMT_CG_rt1": {"2020": [0.0]},
        "_AMT_CG_rt2": {"2020": [0.0]},
        "_AMT_CG_rt2": {"2020": [0.0]},
        "_AMT_CG_rt3": {"2020": [0.0]},
        "_AMT_CG_rt4": {"2020": [0.0]}
    }
}
"""

warning_reform = """
// throws warning but not error
{
    "policy": {
        "_STD_single": {"2020": [1000]}
    }
}
"""

test_coverage_fields = {
    '_state': "<django.db.models.base.ModelState object at 0x10c764950>",
    'creation_date': "datetime.datetime(2015, 1, 1, 0, 0)",
    'id': 64,
    'quick_calc': False,
    'first_year': 2017,
    'CG_nodiff': [False],
    'FICA_ss_trt': [u'*', 0.1, u'*', 0.2],
    'STD_0': [8000.0, '*', 10000.0],
    'ID_BenefitSurtax_Switch_0': [True],
    'ID_Charity_c_cpi': True,
    'EITC_rt_2': [1.0]
}

test_coverage_reform = {
    '_CG_nodiff': {'2017': [False]},
    '_FICA_ss_trt': {'2020': [0.2], '2018': [0.1]},
    '_STD_single': {'2017': [8000.0], '2019': [10000.0]},
    '_ID_Charity_c_cpi': {'2017': True},
    '_ID_BenefitSurtax_Switch_medical': {'2017': [True]},
    '_EITC_rt_2kids': {'2017': [1.0]}
}

test_coverage_map_back_to_tb = {

}


test_coverage_json_reform = """
{
    "policy": {
        "_ID_BenefitSurtax_Switch_charity": {
            "2017": [
                0.0
            ]
        },
        "_ALD_InvInc_ec_base_RyanBrady": {
            "2017": [
                false
            ]
        },
        "_ID_BenefitSurtax_Switch_interest": {
            "2017": [
                0.0
            ]
        },
        "_EITC_indiv": {
            "2017": [
                false
            ]
        },
        "_ID_BenefitSurtax_Switch_misc": {
            "2017": [
                0.0
            ]
        },
        "_ID_BenefitCap_Switch_charity": {
            "2017": [
                0.0
            ]
        },
        "_STD_single": {
            "2017": [
                10000.0
            ]
        },
        "_II_no_em_nu18": {
            "2017": [
                false
            ]
        },
        "_ID_BenefitSurtax_Switch_realestate": {
            "2017": [
                0.0
            ]
        },
        "_ID_BenefitCap_Switch_misc": {
            "2017": [
                0.0
            ]
        },
        "_CG_nodiff": {
            "2017": [
                false
            ]
        },
        "_ID_BenefitSurtax_Switch_statelocal": {
            "2017": [
                0.0
            ]
        },
        "_ID_BenefitCap_Switch_medical": {
            "2017": [
                0.0
            ]
        },
        "_FICA_ss_trt": {
            "2020": [
                0.2
            ],
            "2018": [
                0.1
            ]
        },
        "_ID_BenefitCap_Switch_casualty": {
            "2017": [
                0.0
            ]
        },
        "_ID_Charity_c_cpi": {
            "2017": true
        },
        "_ID_BenefitCap_Switch_statelocal": {
            "2017": [
                0.0
            ]
        },
        "_EITC_rt_2kids": {
            "2017": [
                1.0
            ]
        },
        "_ID_BenefitSurtax_Switch_casualty": {
            "2017": [
                0.0
            ]
        },
        "_NIIT_PT_taxed": {
            "2017": [
                false
            ]
        },
        "_ID_BenefitSurtax_Switch_medical": {
            "2017": [
                1.0
            ]
        },
        "_ID_BenefitCap_Switch_interest": {
            "2017": [
                0.0
            ]
        },
        "_CTC_new_refund_limited": {
            "2017": [
                false
            ]
        },
        "_ID_BenefitCap_Switch_realestate": {
            "2017": [
                0.0
            ]
        }
    }
}
"""

test_coverage_json_assumptions = """
{
    "growdiff_response": {},
    "consumption": {},
    "behavior": {},
    "growdiff_baseline": {}
}
"""

map_back_to_tb = {
    u'_ID_BenefitSurtax_Switch_charity': 'ID_BenefitSurtax_Switch_6',
    '_ALD_InvInc_ec_base_RyanBrady': 'ALD_InvInc_ec_base_RyanBrady',
    u'_ID_BenefitSurtax_Switch_interest': 'ID_BenefitSurtax_Switch_5',
    '_EITC_indiv': 'EITC_indiv',
    u'_ID_BenefitSurtax_Switch_misc': 'ID_BenefitSurtax_Switch_4',
    u'_ID_BenefitCap_Switch_charity': 'ID_BenefitCap_Switch_6',
    u'_STD_single': 'STD_0',
    '_II_no_em_nu18': 'II_no_em_nu18',
    u'_ID_BenefitSurtax_Switch_realestate': 'ID_BenefitSurtax_Switch_2',
    u'_ID_BenefitCap_Switch_misc': 'ID_BenefitCap_Switch_4',
    '_CG_nodiff': 'CG_nodiff',
    u'_ID_BenefitSurtax_Switch_statelocal': 'ID_BenefitSurtax_Switch_1',
    u'_ID_BenefitCap_Switch_medical': 'ID_BenefitCap_Switch_0',
    '_FICA_ss_trt': 'FICA_ss_trt',
    u'_ID_BenefitCap_Switch_casualty': 'ID_BenefitCap_Switch_3',
    '_ID_Charity_c_cpi': 'ID_Charity_c_cpi',
    u'_ID_BenefitCap_Switch_statelocal': 'ID_BenefitCap_Switch_1',
    u'_EITC_rt_2kids': 'EITC_rt_2',
    u'_ID_BenefitSurtax_Switch_casualty': 'ID_BenefitSurtax_Switch_3',
    '_NIIT_PT_taxed': 'NIIT_PT_taxed',
    u'_ID_BenefitSurtax_Switch_medical': 'ID_BenefitSurtax_Switch_0',
    u'_ID_BenefitCap_Switch_interest': 'ID_BenefitCap_Switch_5',
    '_CTC_new_refund_limited': 'CTC_new_refund_limited',
    u'_ID_BenefitCap_Switch_realestate': 'ID_BenefitCap_Switch_2',
    u'_STD_single': 'STD_0',
    u'_STD_headhousehold': 'STD_3',
    u'_II_brk4_single': 'II_brk4_0'
}

test_coverage_exp_read_json_reform = {
    2017: {u'_EITC_rt': [[0.0765, 0.34, 1.0, 0.45]],
           u'_NIIT_PT_taxed': [False],
           u'_ID_BenefitCap_Switch': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
           u'_ALD_InvInc_ec_base_RyanBrady': [False],
           u'_EITC_indiv': [False],
           u'_ID_BenefitSurtax_Switch': [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
           u'_STD': [[10000.0, 12700.0, 6350.0, 9350.0, 12700.0]],
           u'_II_no_em_nu18': [False],
           u'_ID_Charity_c_cpi': True,
           u'_CG_nodiff': [False],
           u'_CTC_new_refund_limited': [False]},
    2018: {u'_FICA_ss_trt': [0.1]},
    2020: {u'_FICA_ss_trt': [0.2]}
}
