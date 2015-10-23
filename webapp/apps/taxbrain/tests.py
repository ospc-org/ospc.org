from django.test import TestCase

from .models import TaxSaveInputs
from .models import convert_to_floats
from .helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                     format_csv)
import taxcalc

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

        ans = package_up_vars(values)

        exp =  [[36000, 72250, 36500, 50200, 74900, 37450],
                [38000, 74000, None, None, None, None],
                [40000, None, None, None, None, None]]

        assert ans['_II_brk2'] == exp
        assert len(ans) == 1

    def test_package_up_vars_CTC(self):
        values = {"CTC_c": [2000.0]}
        ans = package_up_vars(values)
        exp =  [2000.0]
        assert ans['_CTC_c'] == exp

    def test_package_up_vars_with_cpi(self):
        values = {"CTC_c_cpi": True}
        ans = package_up_vars(values)
        assert ans == {'_CTC_c_cpi': True}


    def test_convert_4_budget_years(self):
        values = {"II_brk2_0": [36000., 38000., 40000., 41000],
                    "II_brk2_1": [72250., 74000.],
                    "II_brk2_2": [36500.]
                    }

        ans = package_up_vars(values)

        exp =  [[36000, 72250, 36500, 50200, 74900, 37450],
                [38000, 74000, None, None, None, None],
                [40000, None, None, None, None, None],
                [41000, None, None, None, None, None]]

        assert ans['_II_brk2'] == exp

    def test_convert_multiple_items(self):
        values = {"II_brk2_0": [36000., 38000., 40000., 41000],
                    "II_brk2_1": [72250., 74000.],
                    "II_brk2_2": [36500.]
                    }

        values['II_em'] = [4000]

        ans = package_up_vars(values)

        defaults = taxcalc.policy.Policy.default_data(start_year=2015)

        exp =  [[36000, 72250, 36500, 50200, 74900, 37450],
                [38000, 74000, None, None, None, None],
                [40000, None, None, None, None, None],
                [41000, None, None, None, None, None]]

        assert ans['_II_brk2'] == exp
        exp_em = defaults['_II_em']
        exp_em[0] = 4000
        assert ans['_II_em'] == exp_em
        assert len(ans) == 2

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

        tax_results = {}
        tax_results[u'fiscal_tots'] = [1,2,3]
        tax_results[u'mY_bin'] = { k:[next(c)] for k in bin_keys}
        tax_results[u'mX_bin'] = { k:[next(c)] for k in bin_keys}
        tax_results[u'df_bin'] = { k:[next(c)] for k in bin_keys}
        tax_results[u'mY_dec'] = { k:[next(c)] for k in dec_keys}
        tax_results[u'mX_dec'] = { k:[next(c)] for k in dec_keys}
        tax_results[u'df_dec'] = { k:[next(c)] for k in dec_keys}

        ans = format_csv(tax_results, u'42')
        assert ans[0] == ['#URL: http://www.ospc.org/taxbrain/42/']


        def test_arrange_totals_by_row(self):
            total_row_names = ["ind_tax", "payroll_tax", "combined_tax"]
            tots = {'ind_tax_0': "1", 'ind_tax_1': "2", 'ind_tax_2': "3", 
                    'payroll_tax_0': "4", 'payroll_tax_1': "5", 'payroll_tax_2': "6", 
                    'combined_tax_0': "7", 'combined_tax_1': "8", 'combined_tax_2': "9"}
            ans = arrange_totals_by_row(tots, total_row_names)
            exp = {'ind_tax': ["1", "2", "3"], 'payroll_tax': ["4", "5", "6"], 'combined_tax': ["7", "8", "9"]}
            assert ans == exp

