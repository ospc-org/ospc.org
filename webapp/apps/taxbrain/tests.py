from django.test import TestCase

from .models import TaxSaveInputs
from .models import convert_to_floats
from .helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                     format_csv, arrange_totals_by_row, default_taxcalc_data)
import taxcalc
from taxcalc import Policy

FBY = 2015

def cycler(max):
    count = 0
    while True:
        yield count
        count = (count + 1) % max

class TaxInputTests(TestCase):


    def test_convert(self):

        values = {"II_brk2_0": [36000., 38000., 40000.],
                    "II_brk2_1": [72250., 74000.],
                    "II_brk2_2": [36500.]
                    }

        ans = package_up_vars(values, first_budget_year=FBY)
        pp = Policy(start_year=2013)
        pp.set_year(FBY)
        # irates are rates for 2015, 2016, and 2017
        irates = pp.indexing_rates_for_update(param_name='II_brk2', calyear=FBY,
                                            num_years_to_expand=3)

        # User choices propagate through to all future years
        # The user has specified part of the parameter up to 2017.
        # So, we choose to fill in the propagated value, which is
        # either inflated or not.

        f2_2016 = int(36500 * (1.0 + irates[0]))
        f3_2016 = int(50200 * (1.0 + irates[0]))
        f4_2016 = int(74900 * (1.0 + irates[0]))
        f5_2016 = int(37450 * (1.0 + irates[0]))

        f1_2017 = int(74000 * (1.0 + irates[1]))
        f2_2017 = int(f2_2016 * (1.0 + irates[1]))
    
        exp =  [[36000, 72250, 36500, 50200, 74900, 37450],
                [38000, 74000, f2_2016, 50400, 75300, 37650],
                [40000, f1_2017, f2_2017, None, None, None]]

        assert ans['_II_brk2'] == exp
        assert len(ans) == 1


    def test_package_up_vars_CTC(self):
        values = {"CTC_c": [2000.0]}
        ans = package_up_vars(values, first_budget_year=FBY)
        exp =  [2000.0]
        assert ans['_CTC_c'] == exp

    def test_package_up_vars_with_cpi(self):
        values = {"CTC_c_cpi": True}
        ans = package_up_vars(values, first_budget_year=FBY)
        assert ans == {'_CTC_c_cpi': True}


    def test_convert_4_budget_years(self):
        values = {"II_brk2_0": [36000., 38000., 40000., 41000],
                    "II_brk2_1": [72250., 74000.],
                    "II_brk2_2": [36500.]
                    }

        ans = package_up_vars(values, first_budget_year=FBY)

        pp = Policy(start_year=2013)
        pp.set_year(FBY)
        # irates are rates for 2015, 2016, and 2017
        irates = pp.indexing_rates_for_update(param_name='II_brk2', calyear=FBY,
                                            num_years_to_expand=4)

        # User choices propagate through to all future years
        # The user has specified part of the parameter up to 2017.
        # So, we choose to fill in the propagated value, which is
        # either inflated or not.

        f2_2016 = int(36500 * (1.0 + irates[0]))
        f3_2016 = int(50200 * (1.0 + irates[0]))
        f4_2016 = int(74900 * (1.0 + irates[0]))
        f5_2016 = int(37450 * (1.0 + irates[0]))

        f1_2017 = int(74000 * (1.0 + irates[1]))
        f2_2017 = int(f2_2016 * (1.0 + irates[1]))

        f1_2018 = int(f1_2017 * (1.0 + irates[2]))
        f2_2018 = int(f2_2017 * (1.0 + irates[2]))
    
        exp =  [[36000, 72250, 36500, 50200, 74900, 37450],
                [38000, 74000, f2_2016, 50400, 75300, 37650],
                [40000, f1_2017, f2_2017, None, None, None],
                [41000, f1_2018, f2_2018, None, None, None]]

        assert ans['_II_brk2'] == exp

    def test_convert_multiple_items(self):
        values = {"II_brk2_0": [36000., 38000., 40000., 41000],
                    "II_brk2_1": [72250., 74000.],
                    "II_brk2_2": [36500.]
                    }

        values['II_em'] = [4000]

        ans = package_up_vars(values, first_budget_year=FBY)

        defaults = taxcalc.policy.Policy.default_data(start_year=FBY)

        pp = Policy(start_year=2013)
        pp.set_year(FBY)
        # irates are rates for 2015, 2016, and 2017
        irates = pp.indexing_rates_for_update(param_name='II_brk2', calyear=FBY,
                                            num_years_to_expand=4)

        # User choices propagate through to all future years
        # The user has specified part of the parameter up to 2017.
        # So, we choose to fill in the propagated value, which is
        # either inflated or not.

        f2_2016 = int(36500 * (1.0 + irates[0]))
        f3_2016 = int(50200 * (1.0 + irates[0]))
        f4_2016 = int(74900 * (1.0 + irates[0]))
        f5_2016 = int(37450 * (1.0 + irates[0]))

        f1_2017 = int(74000 * (1.0 + irates[1]))
        f2_2017 = int(f2_2016 * (1.0 + irates[1]))

        f1_2018 = int(f1_2017 * (1.0 + irates[2]))
        f2_2018 = int(f2_2017 * (1.0 + irates[2]))

        exp =  [[36000, 72250, 36500, 50200, 74900, 37450],
                [38000, 74000, f2_2016, 50400, 75300, 37650],
                [40000, f1_2017, f2_2017, None, None, None],
                [41000, f1_2018, f2_2018, None, None, None]]

        assert ans['_II_brk2'] == exp

        # For scalar parameter values, we still have that all user
        # choices propagate up through whatever is specified as 
        # a default. We know that _II_em is specified up to 2016, so
        # package up vars needs to overwrite those default and return
        # 2015 and 2016 values

        exp_em = [4000, int(4000 *(1 + irates[0]))]
        assert ans['_II_em'] == exp_em
        assert len(ans) == 2

    def test_convert_non_cpi_inflated(self):
        values = {"FEI_ec_c": [100000.]}

        ans = package_up_vars(values, first_budget_year=FBY)

        defaults = taxcalc.policy.Policy.default_data(start_year=2015)

        pp = Policy(start_year=2013)
        pp.set_year(FBY)
        # irates are rates for 2015, 2016, and 2017
        irates = pp.indexing_rates_for_update(param_name='FEI_ec_c', calyear=FBY,
                                            num_years_to_expand=2)

        # User choices propagate through to all future years
        # The user has specified the parameter just for 2015, but
        # the defaults JSON file has values up to 2016. We should
        # give back values up to 2016, with user choice propagating

        f2_2016 = 100000

        exp =  [100000, f2_2016]
        assert ans['_FEI_ec_c'] == exp

    def test_package_up_vars_Behavioral_params(self):
        user_values = {'FICA_ss_trt': [0.11],
                       'BE_inc': [0.04]}
        ans = package_up_vars(user_values, first_budget_year=FBY)
        assert ans['_BE_inc'] == [0.04]


    def test_package_up_vars_multi_year(self):
        user_values = {'SS_Earnings_c': [118500, 999999]}
        ans = package_up_vars(user_values, first_budget_year=2016)
        import pdb;pdb.set_trace()
        assert ans['_SS_Earnings_c'] == [118500.0, 999999.0]

    def test_expand1d(self):
        x = [1, 2, 3]
        assert expand_1D(x, 5) == [1, 2, 3, None, None]

    def test_expand2d(self):
        x = [[1, 2, 3], [4, 5, 6]]
        exp = [[1, 2, 3], [4, 5, 6], [None, None, None]]
        assert expand_2D(x, 3) == exp

    def test_expand_list_1(self):
        x = [1, 2, 3]
        assert expand_list(x, 5) == [1, 2, 3, None, None]

    def test_expand2d(self):
        x = [[1, 2, 3], [4, 5, 6]]
        exp = [[1, 2, 3], [4, 5, 6], [None, None, None]]
        assert expand_list(x, 3) == exp

    def test_format_csv(self):
        c = cycler(40)
        tab_types = [u'mY_bin', u'mX_bin', u'mY_dec', u'mX_dec', u'df_dec',
                    u'df_bin', u'fiscal_tots']

        bin_keys = [u'thirty_forty_2', u'thirty_forty_0', u'thirty_forty_1',
                    u'seventyfive_hundred_2',
                    u'forty_fifty_2', u'forty_fifty_1', u'forty_fifty_0',
                    u'ten_twenty_2',
                    u'ten_twenty_0', u'ten_twenty_1', u'hundred_twohundred_0',
                    u'hundred_twohundred_1',
                    u'seventyfive_hundred_1', u'seventyfive_hundred_0',
                    u'twenty_thirty_0', u'twenty_thirty_1', u'twenty_thirty_2',
                    u'fifty_seventyfive_2', u'fifty_seventyfive_1',
                    u'fifty_seventyfive_0', u'twohundred_fivehundred_2',
                    u'twohundred_fivehundred_0', u'twohundred_fivehundred_1',
                    u'thousand_up_2', u'thousand_up_0', u'thousand_up_1',
                    u'less_than_10_2', u'fivehundred_thousand_2',
                    u'fivehundred_thousand_0', u'fivehundred_thousand_1',
                    u'hundred_twohundred_2', u'less_than_10_1', u'less_than_10_0',
                    u'all_1', u'all_0', u'all_2']

        dec_keys = [u'perc20-30_0', u'perc20-30_1', u'perc20-30_2', u'perc50-60_0',
                    u'perc50-60_1', u'perc50-60_2', u'perc40-50_0', u'perc40-50_1',
                    u'perc40-50_2', u'perc90-100_0', u'perc90-100_1',
                    u'perc90-100_2', u'perc30-40_0', u'perc30-40_1',
                    u'perc30-40_2', u'perc0-10_1', u'perc0-10_0', u'perc0-10_2',
                    u'perc70-80_0', u'perc70-80_1', u'perc70-80_2', u'all_1',
                    u'all_0', u'all_2', u'perc80-90_0', u'perc80-90_1',
                    u'perc80-90_2', u'perc10-20_0', u'perc10-20_1', u'perc10-20_2',
                    u'perc60-70_0', u'perc60-70_1', u'perc60-70_2']

        tot_keys = [u'combined_tax', u'ind_tax', u'payroll_tax']

        tax_results = {}
        tax_results[u'fiscal_tots'] = {k:[1,2,3] for k in tot_keys}
        tax_results[u'mY_bin'] = { k:[next(c)] for k in bin_keys}
        tax_results[u'mX_bin'] = { k:[next(c)] for k in bin_keys}
        tax_results[u'df_bin'] = { k:[next(c)] for k in bin_keys}
        tax_results[u'mY_dec'] = { k:[next(c)] for k in dec_keys}
        tax_results[u'mX_dec'] = { k:[next(c)] for k in dec_keys}
        tax_results[u'df_dec'] = { k:[next(c)] for k in dec_keys}

        ans = format_csv(tax_results, u'42', first_budget_year=FBY)
        assert ans[0] == ['#URL: http://www.ospc.org/taxbrain/42/']


    def test_arrange_totals_by_row(self):
        total_row_names = ["ind_tax", "payroll_tax", "combined_tax"]
        tots = {'ind_tax_0': "1", 'ind_tax_1': "2", 'ind_tax_2': "3", 
                'payroll_tax_0': "4", 'payroll_tax_1': "5", 'payroll_tax_2': "6", 
                'combined_tax_0': "7", 'combined_tax_1': "8", 'combined_tax_2': "9"}
        ans = arrange_totals_by_row(tots, total_row_names)
        exp = {'ind_tax': ["1", "2", "3"], 'payroll_tax': ["4", "5", "6"], 'combined_tax': ["7", "8", "9"]}
        assert ans == exp

    def test_default_taxcalc_data(self):
        import math
        dd = default_taxcalc_data(taxcalc.policy.Policy, start_year=2017)
        dd_raw = taxcalc.policy.Policy.default_data(start_year=2017)
        dd_meta = default_taxcalc_data(taxcalc.policy.Policy, start_year=2017, metadata=True)
        floored_std_aged = list(map(math.floor, dd['_STD_Aged'][0]))
        assert dd['_STD_Aged'] == [floored_std_aged]
        assert dd_meta['_STD_Aged']['value'] == [floored_std_aged]

        floored_ii_em_ps = list(map(math.floor, dd['_II_em_ps'][0]))
        assert dd['_II_em_ps'] == [floored_ii_em_ps]
        assert dd_meta['_II_em_ps']['value'] == [floored_ii_em_ps]

        floored_ii_em = [math.floor(dd['_II_em'][0])]
        assert dd['_II_em'] == floored_ii_em
        assert dd_meta['_II_em']['value'] == floored_ii_em

        assert dd_raw['_II_rt6'] == dd['_II_rt6']
