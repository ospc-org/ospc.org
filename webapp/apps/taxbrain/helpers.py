from collections import namedtuple
import numbers
import os
import pandas as pd
import dropq
import sys
import time

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['numba', 'numba.jit', 'numba.vectorize', 'numba.guvectorize',
                'matplotlib', 'matplotlib.pyplot', 'mpl_toolkits', 'mpl_toolkits.mplot3d']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

import taxcalc
from taxcalc import Policy
START_YEAR = int(os.environ.get('START_YEAR', 2016))
PYTHON_MAJOR_VERSION = sys.version_info.major
INT_TO_NTH_MAP = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth',
                  'seventh', 'eighth', 'nineth', 'tenth']

def int_to_nth(x):
    if x < 1:
        return None
    elif x < 11:
        return INT_TO_NTH_MAP[x - 1]
    else:
        # we need to use an inflection library to support any value
        raise NotImplementedError("Not implemented for x > 10")

def is_number(x):
    return isinstance(x, numbers.Number)

def is_string(x):
    if PYTHON_MAJOR_VERSION == 2:
        return isinstance(x, basestring)
    elif PYTHON_MAJOR_VERSION == 3:
        return isinstance(x, str)

def string_to_float(x):
    return float(x.replace(',', ''))

def string_to_float_array(s):
    if len(s) > 0:
        return [float(x) for x in s.split(',')]
    else:
        return []

def same_version(v1, v2):
    idx = v1.rfind('.')
    return v1[:idx] == v2[:idx]

def arrange_totals_by_row(tots, keys):

    out = {}
    for key in keys:
        order_map = {}
        for name in tots:
            if name.startswith(key):
                year_num = int(name[name.rfind('_')+1:])
                order_map[year_num] = tots[name]
        vals = [order_map[i] for i in range(len(order_map))]
        out[key] = vals
    return out

def round_gt_one_to_nearest_int(values):
    ''' round every value to the nearest integer '''
    def round_gt_one(x):
        if x >= 1.0:
            return round(x)
        else:
            return x
    try:
        rounded = map(round_gt_one, values)
    except TypeError:
        rounded = [map(round_gt_one, val) for val in values]

    return rounded


def default_taxcalc_data(cls, start_year, metadata=False):
    ''' Call the default data function on the given class for the given
        start year with meatadata flag
    '''
    dd = cls.default_data(metadata=metadata, start_year=start_year)
    if metadata:
        for k in dd:
            dd[k]['value'] = round_gt_one_to_nearest_int(dd[k]['value'])
    else:
        for k in dd:
            dd[k] = round_gt_one_to_nearest_int(dd[k])
    return dd


#
# Prepare user params to send to DropQ/Taxcalc
#

tcversion_info = taxcalc._version.get_versions()
taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])

TAXCALC_COMING_SOON_FIELDS = [
    '_Dividend_rt1', '_Dividend_thd1',
    '_Dividend_rt2', '_Dividend_thd2',
    '_Dividend_rt3', '_Dividend_thd3',
    '_BE_CG_trn', '_FEI_ec_c'
    ]

TAXCALC_HIDDEN_FIELDS = [
    '_ACTC_Income_thd',
    '_AMT_Child_em', '_AMT_em_pe', '_AMT_thd_MarriedS',
    '_CDCC_ps', '_CDCC_crt',
    '_DCC_c',
    '_EITC_InvestIncome_c', '_EITC_ps_MarriedJ',
    '_ETC_pe_Single', '_ETC_pe_Married',
    '_KT_c_Age',
    '_LLC_Expense_c'
]

TAXCALC_COMING_SOON_INDEXED_BY_MARS = [
    '_Dividend_thd1','_Dividend_thd2', '_Dividend_thd3'
]

#
# Display TaxCalc result data
#

TAXCALC_RESULTS_START_YEAR = START_YEAR
TAXCALC_RESULTS_MTABLE_COL_LABELS = taxcalc.TABLE_LABELS
TAXCALC_RESULTS_DFTABLE_COL_LABELS = taxcalc.DIFF_TABLE_LABELS
TAXCALC_RESULTS_MTABLE_COL_FORMATS = [
    #   divisor,   unit,   decimals
    [      1000,      None, 0], # 'Returns',
    [1000000000, 'Dollars', 1],  # 'AGI',
    [      1000,      None, 0],  # 'Standard Deduction Filers',
    [1000000000, 'Dollars', 1],  # 'Standard Deduction',
    [      1000,      None, 0],  # 'Itemizers',
    [1000000000, 'Dollars', 1],  # 'Itemized Deduction',
    [1000000000, 'Dollars', 1],  # 'Personal Exemption',
    [1000000000, 'Dollars', 1],  # 'Taxable Income',
    [1000000000, 'Dollars', 1],  # 'Regular Tax',
    [1000000000, 'Dollars', 1],  # 'AMTI',
    [      1000,      None, 0],  # 'AMT Filers',
    [1000000000, 'Dollars', 1],  # 'AMT',
    [1000000000, 'Dollars', 1],  # 'Tax before Credits',
    [1000000000, 'Dollars', 1],  # 'Non-refundable Credits',
    [1000000000, 'Dollars', 1],  # 'Tax before Refundable Credits',
    [1000000000, 'Dollars', 1],  # 'Refundable Credits',
    [1000000000, 'Dollars', 1],  # 'Individual Income Liabilities',
    [1000000000, 'Dollars', 1],  # 'Payroll Tax Liablities',
    [1000000000, 'Dollars', 1],  # 'Combined Payroll and individual Income Tax Liablities'
                                      
]
TAXCALC_RESULTS_DFTABLE_COL_FORMATS = [
    [      1000,      None, 0],    # "Inds. w/ Tax Cut",
    [      1000,      None, 0],    # "Inds. w/ Tax Increase",
    [      1000,      None, 0],    # "Count",
    [         1, 'Dollars', 0],  # "Mean Tax Difference",
    [1000000000, 'Dollars', 1],  # "Total Tax Difference",
    [         1,   '%', 1],  # "%age Tax Increase",
    [         1,   '%', 1],  # "%age Tax Decrease",
    [         1,   '%', 1],  # "Share of Overall Change"
]
TAXCALC_RESULTS_BIN_ROW_KEYS = dropq.dropq.bin_row_names
TAXCALC_RESULTS_BIN_ROW_KEY_LABELS = {
    'less_than_10':'Less than 10',
    'ten_twenty':'10-20',
    'twenty_thirty':'20-30',
    'thirty_forty':'30-40',
    'forty_fifty':'40-50',
    'fifty_seventyfive':'50-75',
    'seventyfive_hundred':'75-100',
    'hundred_twohundred':'100-200',
    'twohundred_fivehundred':'200-500',
    'fivehundred_thousand':'500-1000',
    'thousand_up':'1000+',
    'all':'All'
}
TAXCALC_RESULTS_DEC_ROW_KEYS = dropq.dropq.decile_row_names
TAXCALC_RESULTS_DEC_ROW_KEY_LABELS = {
    'perc0-10':'0-10%',
    'perc10-20':'10-20%',
    'perc20-30':'20-30%',
    'perc30-40':'30-40%',
    'perc40-50':'40-50%',
    'perc50-60':'50-60%',
    'perc60-70':'60-70%',
    'perc70-80':'70-80%',
    'perc80-90':'80-90%',
    'perc90-100':'90-100%',
    'all':'All'
}
TAXCALC_RESULTS_TABLE_LABELS = {
    'mX_dec': 'Base plan tax vars, weighted avg per expanded income decile',
    'mY_dec': 'User plan tax vars, weighted avg per expanded income decile',
    'df_dec': 'Individual Income Tax: Difference between Base and User plans by expanded income decile',
    'pdf_dec': 'Payroll Tax: Difference between Base and User plans by expanded income decile',
    'cdf_dec': 'Combined Payroll and Individual Income Tax: Difference between Base and User plans by expanded income decile',
    'mX_bin': 'Base plan tax vars, weighted avg per expanded income bin',
    'mY_bin': 'User plan tax vars, weighted avg per expanded income bin',
    'df_bin': 'Individual Income Tax: Difference between Base and User plans by expanded income bin',
    'pdf_bin': 'Payroll Tax: Difference between Base and User plans by expanded income bin',
    'cdf_bin': 'Combined Payroll and Individual Income Tax: Difference between Base and User plans by expanded income bin',
    'fiscal_tots': 'Total Liabilities Change by Calendar Year',
}
TAXCALC_RESULTS_TOTAL_ROW_KEYS = dropq.dropq.total_row_names
TAXCALC_RESULTS_TOTAL_ROW_KEY_LABELS = {
    'ind_tax':'Individual Income Tax Liability Change',
    'payroll_tax':'Payroll Tax Liability Change',
    'combined_tax':'Combined Payroll and Individual Income Tax Liability Change',
}

def expand_1D(x, num_years):
    """
    Expand the given data to account for the given number of budget years.
    Expanded entries are None by default
    """

    if len(x) >= num_years:
        return list(x)
    else:
        ans = [None] * num_years
        ans[:len(x)] = x
        return ans


def expand_2D(x, num_years):
    """
    Expand the given data to account for the given number of budget years.
    For 2D arrays, we expand out the number of rows until we have num_years
    number of rows. Added rows have all 'None' entries
    """

    if len(x) >= num_years:
        return list(x)
    else:
        ans = []
        for i in range(0, num_years):
            ans.append([None] * len(x[0]))
        for i, arr in enumerate(x):
            ans[i] = arr
        return ans


def expand_list(x, num_years):
    """
    Dispatch to either expand_1D or expand2D depending on the dimension of x

    Parameters:
    -----------
    x : value to expand

    num_years: int
    Number of budget years to expand

    Returns:
    --------
    expanded list
    """
    if isinstance(x[0], list):
        return expand_2D(x, num_years)
    else:
        return expand_1D(x, num_years)


def propagate_user_list(x, num_years, cpi, first_budget_year):
    """
    Dispatch to either expand_1D or expand2D depending on the dimension of x

    Parameters:
    -----------
    x : list from user to progagate forward in time. The first value is for
        year 'first_budget_year'. The value at index i is the value for
        budget year first_budget_year + i. 

    num_years: int 
               Number of budget years to expand

    cpi: Bool

    first_budget_year: int 

    Returns:
    --------
    list of length 'num_years'. if 'cpi'==True, the values will be inflated
    based on the last value the user specified

    """
    # x can't be empty
    assert x

    pp = Policy(start_year=2013)
    pp.set_year(first_budget_year)
    # irates are rates for 2015, 2016, and 2017
    if cpi:
        irates = pp.indexing_rates_for_update(param_name='II_brk2',
                                              calyear=first_budget_year,
                                              num_years_to_expand=num_years)
    else:
        irates = [0.0] * num_years

    last_val = x[-1]
    ans = [None] * num_years
    for i in range(num_years):
        if i < len(x):
            ans[i] = x[i]
        else:
            ans[i] = int(ans[i-1] * (1.0 + irates[i-1]))

    return ans


def convert_to_floats(tsi):
    """
    A helper function that tax all of the fields of a TaxSaveInputs model
    and converts them to floats, or list of floats
    """
    def numberfy_one(x):
        if isinstance(x, float):
            return x
        else:
            return float(x)

    def numberfy(x):
        if isinstance(x, list):
            return [numberfy_one(i) for i in x]
        else:
            return numberfy_one(x)

    attrs = vars(tsi)
    return { k:numberfy(v) for k,v in attrs.items() if v}


def leave_name_in(key, val, dd):
    """
    Under certain conditions, we will remove 'key' and its value
    from the dictionary we pass to the dropq package. This function
    will test those conditions and return a Bool.

    Parameters:
    -----------
    key: a field name to potentially pass to the dropq package

    dd: the default dictionary of data in taxcalc Parameters

    Returns:
    --------
    Bool: True if we allow this field to get passed on. False
          if it should be removed.
    """

    if key in dd:
        return True
    elif key in ["elastic_gdp"]:
        return True
    else:
        print "Don't have this pair: ", key, val
        underscore_name_in_defaults = "_" + key in dd
        is_cpi_name = key.endswith("_cpi")
        is_array_name = (key.endswith("_0") or key.endswith("_1") or
                         key.endswith("_2") or key.endswith("_3"))
        if (underscore_name_in_defaults or is_cpi_name or is_array_name):
            return True
        else:
            return False


def package_up_vars(user_values, first_budget_year):
    dd = default_taxcalc_data(taxcalc.policy.Policy, start_year=first_budget_year)
    dd_meta = default_taxcalc_data(taxcalc.policy.Policy,
                                   start_year=first_budget_year, metadata=True)
    growth_dd = default_taxcalc_data(taxcalc.growth.Growth,
                                     start_year=first_budget_year)

    behavior_dd = default_taxcalc_data(taxcalc.Behavior, start_year=first_budget_year)
    dd.update(growth_dd)
    dd.update(behavior_dd)
    dd.update({"elastic_gdp":[0.54]})
    dd_meta.update({"elastic_gdp":{'values':[0.54], 'cpi_inflated':False}})
    dd_meta.update(default_taxcalc_data(taxcalc.Behavior,
                                        start_year=first_budget_year,
                                        metadata=True))
    dd_meta.update(default_taxcalc_data(taxcalc.policy.Policy,
                                        start_year=first_budget_year,
                                        metadata=True))
    for k, v in user_values.items():
        if not leave_name_in(k, v, dd):
            print "Removing ", k, v
            del user_values[k]

    def discover_cpi_flag(param):
        ''' Helper function to discover the CPI setting for this parameter'''

        cpi_flag_from_user = user_values.get(param + "_cpi", None)
        if cpi_flag_from_user is None:
            cpi_flag_from_user = user_values.get("_" + param + "_cpi", None)

        if cpi_flag_from_user is None:
            attrs = dd_meta[param]
            cpi_flag = attrs.get('cpi_inflated', False)
        else:
            cpi_flag = cpi_flag_from_user
        return cpi_flag


    name_stems = {}
    ans = {}
    #Find the 'broken out' array values, these have special treatment
    for k, v in user_values.items():
        if (k.endswith("_0") or k.endswith("_1") or k.endswith("_2")
                or k.endswith("_3")):
            vals = name_stems.setdefault(k[:-2], [])
            vals.append(k)

    #For each array value, expand as necessary based on default data
    #then add user values. It is acceptable to leave 'blanks' as None.
    #This is handled on the taxcalc side
    for k, vals in name_stems.items():
        if k in dd:
            default_data = dd[k]
            param = k
        else:
            #add a leading underscore
            default_data = dd["_" + k]
            param = "_" + k

        # Discover the CPI setting for this parameter
        cpi_flag = discover_cpi_flag(param)

        # get max number of years to advance
        _max = 0
        for name in vals:
            num_years = len(user_values[name])
            if num_years > _max:
                _max = num_years
        expnded_defaults = expand_list(default_data, _max)
        #Now copy necessary data to expanded array
        for name in sorted(vals):
            idx = int(name[-1]) # either 0, 1, 2, 3
            user_arr = user_values[name]
            if len(user_arr) < expnded_defaults:
                user_arr = propagate_user_list(user_arr,
                                               num_years=len(expnded_defaults),
                                               cpi=cpi_flag,
                                               first_budget_year=first_budget_year)
            for new_arr, user_val in zip(expnded_defaults, user_arr):
                new_arr[idx] = int(user_val)
            del user_values[name]
        ans[param] = expnded_defaults

    #Process remaining values set by user
    for k, v in user_values.items():
        if k in dd:
            param = k
        elif k.endswith("_cpi"):
            if k[:-4] in dd:
                ans[k] = v
            else:
                ans['_' + k] = v
            continue
        else:
            #add a leading underscore
            param = "_" + k

        default_data = dd[param]

        # Discover the CPI setting for this parameter
        cpi_flag = discover_cpi_flag(param)

        if len(v) < default_data:
            v = propagate_user_list(v,
                                    num_years=len(default_data),
                                    cpi=cpi_flag,
                                    first_budget_year=first_budget_year)

        ans[param] = v

    return ans


#
# Gather data to assist in displaying TaxCalc param form
#

class TaxCalcField(object):
    """
    An atomic unit of data for a TaxCalcParam, which can be stored as a field
    Used for both CSV float fields (value column data) and boolean fields (cpi)
    """
    def __init__(self, id, label, values, param, first_budget_year):
        self.id = id
        self.label = label
        self.values = values
        self.param = param

        self.values_by_year = {}
        for i, value in enumerate(values):
            year = param.start_year + i
            self.values_by_year[year] = value

        self.default_value = self.values_by_year[first_budget_year]


class TaxCalcParam(object):
    """
    A collection of TaxCalcFields that represents all configurable details
    for one of TaxCalc's Parameters
    """
    def __init__(self, param_id, attributes, first_budget_year):
        self.__load_from_json(param_id, attributes, first_budget_year)

    def __load_from_json(self, param_id, attributes, first_budget_year):
        values_by_year = attributes['value']
        col_labels = attributes['col_label']

        self.tc_id = param_id
        self.nice_id = param_id[1:] if param_id[0] == '_' else param_id
        self.name = attributes['long_name']
        self.info = " ".join([
            attributes['description'],
            attributes.get('irs_ref') or "",  # sometimes this is blank
            attributes.get('notes') or ""     # sometimes this is blank
            ]).strip()

        # Pretend the start year is 2015 (instead of 2013),
        # until values for that year are provided by taxcalc
        #self.start_year = int(attributes['start_year'])
        self.start_year = first_budget_year

        self.coming_soon = (self.tc_id in TAXCALC_COMING_SOON_FIELDS)
        self.hidden = (self.tc_id in TAXCALC_HIDDEN_FIELDS)

        # normalize single-year default lists [] to [[]]
        if not isinstance(values_by_year[0], list):
            values_by_year = [values_by_year]

        # organize defaults by column [[A1,B1],[A2,B2]] to [[A1,A2],[B1,B2]]
        values_by_col = [list(x) for x in zip(*values_by_year)]

        #
        # normalize and format column labels
        #
        if self.tc_id in TAXCALC_COMING_SOON_INDEXED_BY_MARS:
            col_labels = ["Single", "Married filing Jointly",
                              "Married filing Separately", "Head of Household"]
            values_by_col = ['0','0','0','0']

        elif isinstance(col_labels, list):
            if col_labels == ["0kids", "1kid", "2kids", "3+kids"]:
                col_labels = ["0 Kids", "1 Kid", "2 Kids", "3+ Kids"]

            elif col_labels == ["single", "joint", "separate", "head of household",
                                "widow", "separate"] or col_labels == \
                               ["single", "joint", "separate", "head of household",
                               "widow", "separate","dependent"]:

                col_labels = ["Single", "Married filing Jointly",
                              "Married filing Separately", "Head of Household"]

        else:
            if col_labels == "NA" or col_labels == "":
                col_labels = [""]
            elif col_labels == "0kids 1kid  2kids 3+kids":
                col_labels =  ["0 Kids", "1 Kid", "2 Kids", "3+ Kids"]


        # create col params
        self.col_fields = []

        if len(col_labels) == 1:
            self.col_fields.append(TaxCalcField(
                self.nice_id,
                col_labels[0],
                values_by_col[0],
                self,
                first_budget_year
            ))
        else:
            for col, label in enumerate(col_labels):
                self.col_fields.append(TaxCalcField(
                    self.nice_id + "_{0}".format(col),
                    label,
                    values_by_col[col],
                    self,
                    first_budget_year
                ))

        # we assume we can CPI inflate if first value isn't a ratio
        first_value = self.col_fields[0].values[0]
        if 'inflatable' in attributes:
            self.inflatable = attributes['inflatable']
        else:
            self.inflatable = first_value > 1 and self.tc_id != '_ACTC_ChildNum'


        if self.inflatable:
            cpi_flag = attributes['cpi_inflated']
            self.cpi_field = TaxCalcField(self.nice_id + "_cpi", "CPI",
                                          [cpi_flag], self, first_budget_year)

        # Get validation details
        validations_json =  attributes.get('validations')
        if validations_json:
            self.max = validations_json.get('max')
            self.min = validations_json.get('min')
        else:
            self.max = None
            self.min = None

        # Coax string-formatted numerics to floats and field IDs to nice IDs
        if self.max:
            if is_string(self.max):
                try:
                    self.max = string_to_float(self.max)
                except ValueError:
                    if self.max[0] == '_':
                        self.max = self.max[1:]

        if self.min:
            if is_string(self.min):
                try:
                    self.min = string_to_float(self.min)
                except ValueError:
                    if self.min[0] == '_':
                        self.min = self.min[1:]


# Create a list of default policy
def default_policy(first_budget_year):

    TAXCALC_DEFAULT_PARAMS_JSON = default_taxcalc_data(taxcalc.policy.Policy,
                                                       metadata=True,
                                                       start_year=first_budget_year)

    default_taxcalc_params = {}
    for k,v in TAXCALC_DEFAULT_PARAMS_JSON.iteritems():
        param = TaxCalcParam(k,v, first_budget_year)
        default_taxcalc_params[param.nice_id] = param

    BEHAVIOR_DEFAULT_PARAMS_JSON = default_taxcalc_data(taxcalc.Behavior,
                                                        metadata=True,
                                                        start_year=first_budget_year)

    for k,v in BEHAVIOR_DEFAULT_PARAMS_JSON.iteritems():
        param = TaxCalcParam(k,v, first_budget_year)
        default_taxcalc_params[param.nice_id] = param

    #Growth assumptions not in default data yet. Add in the appropriate info so that
    #the params dictionary has the right info
    # value, col_label, long_name, description, irs_ref, notes
    growth_params = []
    adj_long_name = ("Deviation from CBO forecast of baseline economic "
                    "growth (percentage point)")
    adj_descr = ("The data underlying this model are extrapolated to roughly "
                "match the CBO's projection of the economy's development over "
                "the 10-year federal budget window, with each type of economic "
                "data extrapolated at a different growth rate. This parameter "
                "allows a factor to be subtracted or added to those growth "
                "rates for the construction of the economic baseline. For "
                "example if you supply .02 (or 2%), then 0.02 will be added to "
                "the wage and salary growth rate, interest income growth rate, "
                "dividend growth rate, schedule E income growth rate, and all "
                "other growth rates used to extrapolate the underlying dataset.")

    factor_adjustment = {'value':[[0]], 'col_label':"", 'long_name': adj_long_name,
                        'description': adj_descr, 'irs_ref':'', 'notes':''}
    growth_params.append(('_factor_adjustment', factor_adjustment))

    target_long_name = ("Replacement for CBO real GDP growth in economic baseline "
                        "(percent)")

    target_descr = ("The data underlying this model are extrapolated to roughly "
                    "match the CBO's projection of the economy's development "
                    "over the 10-year federal budget window, with each type of "
                    "economic data extrapolated at a different growth rate. One "
                    "of the growth rates taken from the CBO is GDP growth. This "
                    "parameter allows you to specify a real GDP growth rate, and "
                    "all other rates will be modified to maintain the distance "
                    "between them and GDP growth in the CBO baseline. For example, "
                    "if the CBO growth rate for one year is 0.02 and the user "
                    "enters 0.018 for this parameter, then 0.002 will be "
                    "subtracted from every growth rate in the construction of the "
                    "economic baseline, including wage and salary growth, interest "
                    "income growth, dividend growth, and many others.")

    factor_target= {'value':[[0]], 'col_label':"", 'long_name': target_long_name,
                        'description': target_descr, 'irs_ref':'', 'notes':''}

    growth_params.append(('_factor_target', factor_target))

    for k,v in growth_params:
        param = TaxCalcParam(k,v, first_budget_year)
        default_taxcalc_params[param.nice_id] = param

    TAXCALC_DEFAULT_PARAMS = default_taxcalc_params

    return TAXCALC_DEFAULT_PARAMS


# Debug TaxParams
"""
for k, param in TAXCALC_DEFAULT_PARAMS.iteritems():
    print(' -- ' + k + ' -- ')
    print('TC id:   ' + param.tc_id)
    print('Nice id: ' + param.nice_id)
    print('name:    ' + param.name)
    print('info:    ' + param.info + '\n')

    if param.inflatable:
        field = param.cpi_field
        print(field.id + ' - ' + field.label + ' - ' + str(field.values))
    for field in param.col_fields:
        print(field.id + '   - ' + field.label + ' - ' + str(field.values))

    print('\n')
"""


def taxcalc_results_to_tables(results, first_budget_year):
    """
    Take various results from dropq, i.e. mY_dec, mX_bin, df_dec, etc
    Return organized and labeled table results for display
    """
    total_row_keys = TAXCALC_RESULTS_TOTAL_ROW_KEYS
    num_years = len(results['fiscal_tots'][total_row_keys[0]])
    years = list(range(first_budget_year,
                       first_budget_year + num_years))

    tables = {}
    for table_id in results:
        # Debug inputs
        """
        print('\n ----- inputs ------- ')
        print('looking at {0}'.format(table_id))
        if table_id == 'fiscal_tots':
            print('{0}'.format(results[table_id]))
        else:
            print('{0}'.format(results[table_id].keys()))
        print(' ----- inputs ------- \n')
        """

        if table_id in ['mX_dec', 'mY_dec']:
            row_keys = TAXCALC_RESULTS_DEC_ROW_KEYS
            row_labels = TAXCALC_RESULTS_DEC_ROW_KEY_LABELS
            col_labels = TAXCALC_RESULTS_MTABLE_COL_LABELS
            col_formats = TAXCALC_RESULTS_MTABLE_COL_FORMATS
            table_data = results[table_id]
            multi_year_cells = True

        elif table_id in ['mX_bin', 'mY_bin']:
            row_keys = TAXCALC_RESULTS_BIN_ROW_KEYS
            row_labels = TAXCALC_RESULTS_BIN_ROW_KEY_LABELS
            col_labels = TAXCALC_RESULTS_MTABLE_COL_LABELS
            col_formats = TAXCALC_RESULTS_MTABLE_COL_FORMATS
            table_data = results[table_id]
            multi_year_cells = True

        elif table_id in ['df_dec', 'pdf_dec', 'cdf_dec']:
            row_keys = TAXCALC_RESULTS_DEC_ROW_KEYS
            row_labels = TAXCALC_RESULTS_DEC_ROW_KEY_LABELS
            col_labels = TAXCALC_RESULTS_DFTABLE_COL_LABELS
            col_formats = TAXCALC_RESULTS_DFTABLE_COL_FORMATS
            table_data = results[table_id]
            multi_year_cells = True

        elif table_id in ['df_bin', 'pdf_bin', 'cdf_bin']:
            row_keys = TAXCALC_RESULTS_BIN_ROW_KEYS
            row_labels = TAXCALC_RESULTS_BIN_ROW_KEY_LABELS
            col_labels = TAXCALC_RESULTS_DFTABLE_COL_LABELS
            col_formats = TAXCALC_RESULTS_DFTABLE_COL_FORMATS
            table_data = results[table_id]
            multi_year_cells = True

        elif table_id == 'fiscal_tots':
            # todo - move these into the above TC result param constants
            row_keys = TAXCALC_RESULTS_TOTAL_ROW_KEYS 
            row_labels = TAXCALC_RESULTS_TOTAL_ROW_KEY_LABELS 
            col_labels = years
            col_formats = [ [1000000000, 'Dollars', 1] for y in years]
            table_data = results[table_id]
            multi_year_cells = False

        table = {
            'col_labels': col_labels,
            'cols': [],
            'label': TAXCALC_RESULTS_TABLE_LABELS[table_id],
            'rows': [],
            'multi_valued': multi_year_cells
        }

        for col_key, label in enumerate(col_labels):
            table['cols'].append({
                'label': label,
                'divisor': col_formats[col_key][0],
                'units': col_formats[col_key][1],
                'decimals': col_formats[col_key][2],
            })

        col_count = len(col_labels)
        for row_key in row_keys:
            row = {
                'label': row_labels[row_key],
                'cells': []
            }

            for col_key in range(0, col_count):
                cell = {
                    'year_values': {},
                    'format': {
                        'divisor': table['cols'][col_key]['divisor'],
                        'decimals': table['cols'][col_key]['decimals'],
                    }
                }

                if multi_year_cells:
                    for yi, year in enumerate(years):
                        value = table_data["{0}_{1}".format(row_key, yi)][col_key]
                        if value[-1] == "%":
                            value = value[:-1]
                        cell['year_values'][year] = value

                    cell['first_value'] = cell['year_values'][first_budget_year]

                else:
                    value = table_data[row_key][col_key]
                    if value[-1] == "%":
                            value = value[:-1]
                    cell['value'] = value

                row['cells'].append(cell)

            table['rows'].append(row)

        tables[table_id] = table

        # Debug results
        """
        print '\n ----- result ------- '
        print '{0}'.format(table)
        print ' ----- result ------- \n'
        """

    tables['result_years'] = years
    return tables

def format_csv(tax_results, url_id, first_budget_year):
    """
    Takes a dictionary with the tax_results, having these keys:
    [u'mY_bin', u'mX_bin', u'mY_dec', u'mX_dec', u'df_dec', u'df_bin',
    u'fiscal_tots']
    And then returns a list of list of strings for CSV output. The format
    of the lines is as follows:
    #URL: http://www.ospc.org/taxbrain/ID/csv/
    #fiscal tots data
    YEAR_0, ... YEAR_K
    val, val, ... val
    #mX_dec
    YEAR_0
    col_0, col_1, ..., col_n
    val, val, ..., val
    YEAR_1
    col_0, col_1, ..., col_n
    val, val, ..., val
    ...
    #mY_dec
    YEAR_0
    col_0, col_1, ..., col_n
    val, val, ..., val
    YEAR_1
    col_0, col_1, ..., col_n
    val, val, ..., val
    ...
    #df_dec
    YEAR_0
    col_0, col_1, ..., col_n
    val, val, ..., val
    YEAR_1
    col_0, col_1, ..., col_n
    val, val, ..., val
    ...
    #mX_bin
    YEAR_0
    col_0, col_1, ..., col_n
    val, val, ..., val
    YEAR_1
    col_0, col_1, ..., col_n
    val, val, ..., val
    ...
    #mY_bin
    YEAR_0
    col_0, col_1, ..., col_n
    val, val, ..., val
    YEAR_1
    col_0, col_1, ..., col_n
    val, val, ..., val
    ...
    #df_bin
    YEAR_0
    col_0, col_1, ..., col_n
    val, val, ..., val
    YEAR_1
    col_0, col_1, ..., col_n
    val, val, ..., val
    ...
    """
    res = []

    #URL
    res.append(["#URL: http://www.ospc.org/taxbrain/" + str(url_id) + "/"])

    #FISCAL TOTS
    res.append(["#fiscal totals data"])
    ft = tax_results.get('fiscal_tots', {})
    yrs = [first_budget_year + i for i in range(0, len(ft['ind_tax']))]
    if yrs:
        res.append(yrs)
    if ft:
        res.append(['payroll_tax'])
        res.append(ft['payroll_tax'])
        res.append(['combined_tax'])
        res.append(ft['combined_tax'])
        res.append(['ind_tax'])
        res.append(ft['ind_tax'])

    #MX_DEC
    res.append(["#mX_dec"])
    mxd = tax_results.get('mX_dec', {})
    if mxd:
        for count, yr in enumerate(yrs):
            res.append([yr])
            res.append(TAXCALC_RESULTS_MTABLE_COL_LABELS)
            for row in TAXCALC_RESULTS_DEC_ROW_KEYS:
                res.append(mxd[row+"_" + str(count)])

    #MY_DEC
    res.append(["#mY_dec"])
    myd = tax_results.get('mY_dec', {})
    if myd:
        for count, yr in enumerate(yrs):
            res.append([yr])
            res.append(TAXCALC_RESULTS_MTABLE_COL_LABELS)
            for row in TAXCALC_RESULTS_DEC_ROW_KEYS:
                res.append(myd[row+"_" + str(count)])

    #DF_DEC
    res.append(["#df_dec"])
    dfd = tax_results.get('df_dec', {})
    if dfd:
        for count, yr in enumerate(yrs):
            res.append([yr])
            res.append(TAXCALC_RESULTS_DFTABLE_COL_LABELS)
            for row in TAXCALC_RESULTS_DEC_ROW_KEYS:
                res.append(dfd[row+"_" + str(count)])

    #MX_BIN
    res.append(["#mX_bin"])
    mxb = tax_results.get('mX_bin', {})
    if mxb:
        for count, yr in enumerate(yrs):
            res.append([yr])
            res.append(TAXCALC_RESULTS_MTABLE_COL_LABELS)
            for row in TAXCALC_RESULTS_BIN_ROW_KEYS:
                res.append(mxb[row+"_" + str(count)])

    #MY_BIN
    res.append(["#mY_bin"])
    myb = tax_results.get('mY_bin', {})
    if myb:
        for count, yr in enumerate(yrs):
            res.append([yr])
            res.append(TAXCALC_RESULTS_MTABLE_COL_LABELS)
            for row in TAXCALC_RESULTS_BIN_ROW_KEYS:
                res.append(myb[row+"_" + str(count)])

    #DF_BIN
    res.append(["#df_bin"])
    dfb = tax_results.get('df_bin', {})
    if dfb:
        for count, yr in enumerate(yrs):
            res.append([yr])
            res.append(TAXCALC_RESULTS_DFTABLE_COL_LABELS)
            for row in TAXCALC_RESULTS_BIN_ROW_KEYS:
                res.append(dfb[row+"_" + str(count)])

    return res
