# Mock some module for imports because we can't fit them on Heroku slugs
import sys
from taxcalc import Policy

from ..taxbrain.helpers import (is_string, string_to_float, is_wildcard)
from ..taxbrain.param_displayers import TaxCalcField
from ..constants import START_YEAR

import btax

PYTHON_MAJOR_VERSION = sys.version_info.major

BTAX_BITR = ['btax_betr_corp',
             'btax_betr_pass',
             'btax_betr_entity_Switch']
BTAX_DEPREC = ['btax_depr_allyr', 'btax_depr_3yr', 'btax_depr_5yr',
               'btax_depr_7yr', 'btax_depr_10yr',
               'btax_depr_15yr', 'btax_depr_20yr', 'btax_depr_25yr',
               'btax_depr_27_5yr', 'btax_depr_39yr']
BTAX_OTHER = ['btax_other_hair', 'btax_other_corpeq',
              'btax_other_proptx', 'btax_other_invest']
BTAX_ECON = ['btax_econ_nomint', 'btax_econ_inflat']


BTAX_VERSION_INFO = btax._version.get_versions()
BTAX_VERSION = BTAX_VERSION_INFO['version']

INT_TO_NTH_MAP = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth',
                  'seventh', 'eighth', 'nineth', 'tenth']
#
# Prepare user params to send to DropQ/Taxcalc
#
class BTaxField(TaxCalcField):

    pass


class BTaxParam(object):

    """
    A collection of TaxCalcFields that represents all configurable details
    for one of TaxCalc's Parameters
    """
    coming_soon = False
    inflatable = False

    def __init__(self, param_id, attributes, start_year=START_YEAR):
        self.__load_from_json(param_id, attributes, int(start_year))

    def __load_from_json(self, param_id, attributes, start_year):
        # TODO does /ccc need to handle
        # budget year /start year logic
        # as in /taxbrain. If so, see
        # TaxCalcParam for changes to
        # make here
        self.start_year = first_budget_year = start_year
        values_by_year = attributes['value']

        self.tc_id = param_id
        self.nice_id = param_id[1:] if param_id[0] == '_' else param_id
        self.name = attributes['long_name']
        self.info = " ".join([
            attributes['description'],
            attributes.get('notes') or ""     # sometimes this is blank
        ]).strip()

        # normalize single-year default lists [] to [[]]
        if not isinstance(values_by_year[0], list):
            values_by_year = [values_by_year]

        # organize defaults by column [[A1,B1],[A2,B2]] to [[A1,A2],[B1,B2]]
        values_by_col = [list(x) for x in zip(*values_by_year)]

        # create col params
        self.col_fields = []
        # get value for appropriate year
        ix = min(start_year - 2015, len(values_by_col) - 1)
        self.col_fields.append(TaxCalcField(
            self.nice_id,
            attributes['description'],
            values_by_col[ix],
            self,
            first_budget_year
        ))

        validations_json = attributes.get('validations')
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


def get_btax_defaults(start_year=START_YEAR):
    from btax import DEFAULTS
    defaults = dict(DEFAULTS)
    # Set Bogus default for now
    defaults['btax_betr_pass']['value'] = [0.0]
    for k, v in list(defaults.items()):
        v['col_label'] = ['']
    BTAX_DEFAULTS = {}

    for k in (BTAX_BITR + BTAX_OTHER + BTAX_ECON):
        param = BTaxParam(k, defaults[k], start_year)
        BTAX_DEFAULTS[param.nice_id] = param
    for k in BTAX_DEPREC:
        fields = ['{}_{}_Switch'.format(k, tag)
                  for tag in ('gds', 'ads', 'tax')]
        for field in fields:
            param = BTaxParam(field, defaults[field], start_year)
            BTAX_DEFAULTS[param.nice_id] = param
        for field in ['{}_{}'.format(k, 'exp')]:
            param = BTaxParam(field, defaults[field], start_year)
            BTAX_DEFAULTS[param.nice_id] = param
    return BTAX_DEFAULTS


BTAX_DEFAULTS = get_btax_defaults()


def hover_args_to_btax_depr():
    # Hover over text
    from btax import DEFAULTS
    hover_notes = {}
    defaults = dict(DEFAULTS)
    hover_notes['gds_note'] = defaults['btax_depr_hover_gds_Switch']['notes']
    hover_notes['ads_note'] = defaults['btax_depr_hover_ads_Switch']['notes']
    hover_notes['economic_note'] = (defaults['btax_depr_hover_tax_Switch']
                                            ['notes'])
    hover_notes['bonus_note'] = defaults['btax_depr_hover_exp']['notes']
    return hover_notes


def group_args_to_btax_depr(btax_default_params, asset_yr_str):
    depr_argument_groups = []
    for yr in asset_yr_str:
        gds_id = 'btax_depr_{}yr_gds_Switch'.format(yr)
        ads_id = 'btax_depr_{}yr_ads_Switch'.format(yr)
        tax_id = 'btax_depr_{}yr_tax_Switch'.format(yr)
        exp_id = 'btax_depr_{}yr_exp'.format(yr)
        radio_group_name = 'btax_depr_{}yr'.format(yr)
        field3_cb = 'btax_depr_{}yr_exp'.format(yr)
        field4_cb = 'btax_depr_{}yr_tax'.format(yr)

        if yr == 'all':
            pretty = "Check all"
            is_check_all = True
            label = ''
            tr_style_class = 'tr-check-all'
        else:
            is_check_all = False
            label = ''
            tr_style_class = ''
            pretty = '{}-year'.format(yr.replace('_', '.'))
        depr_argument_groups.append(
            dict(param1=btax_default_params[gds_id],
                 field1=gds_id,
                 param2=btax_default_params[ads_id],
                 field2=ads_id,
                 param3=btax_default_params[tax_id],
                 field3=tax_id,
                 param4=btax_default_params[exp_id],
                 field4=exp_id,
                 radio_group_name=radio_group_name,
                 asset_yr_str=yr,
                 tr_style_class=tr_style_class,
                 pretty_asset_yr_str=pretty,
                 field3_cb=field3_cb,
                 field4_cb=field4_cb,
                 is_check_all=is_check_all,
                 label=label,
                 td_style_class="table-check-all-item" if yr == 'all' else '')

        )
    return depr_argument_groups


def make_bool(x):
    b = True if x == 'True' else False
    return b


def convert_val(x):
    if is_wildcard(x):
        return x
    try:
        return float(x)
    except ValueError:
        return make_bool(x)


def parameter_name(param):
    if not param.startswith("_"):
        param = "_" + param

    is_multi_param = any(param.endswith("_" + suffix)
                         for suffix in ("0", "1", "2", "3"))
    if is_multi_param:
        return param[:-2]
    else:
        return param


def int_to_nth(x):
    if x < 1:
        return None
    elif x < 11:
        return INT_TO_NTH_MAP[x - 1]
    else:
        # we need to use an inflection library to support any value
        raise NotImplementedError("Not implemented for x > 10")


def string_to_float_array(s):
    if len(s) > 0:
        return [float(x) for x in s.split(',')]
    else:
        return []


def check_wildcards(x):
    if isinstance(x, list):
        return any([check_wildcards(i) for i in x])
    else:
        return is_wildcard(x)


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


def propagate_user_list(x, name, defaults, cpi, first_budget_year,
                        multi_param_idx=-1):
    """
    Dispatch to either expand_1D or expand2D depending on the dimension of x
    Parameters:
    -----------
    x : list from user to propagate forward in time. The first value is for
        year 'first_budget_year'. The value at index i is the value for
        budget year first_budget_year + i.
    defaults: list of default values; our result must be at least this long
    name: the parameter name for looking up the indexing rate
    cpi: Bool
    first_budget_year: int
    multi_param_idx: int, optional. If this parameter is multi-valued, this
        is the index for which the values for 'x' apply. So, for exampe, if
        multi_param_idx=0, the values for x are typically for the 'single'
        filer status. -1 indidcates that this is not a multi-valued
        parameter
    Returns:
    --------
    list of length 'num_years'. if 'cpi'==True, the values will be inflated
    based on the last value the user specified
    """
    # x must have a real first value
    assert len(x) > 0
    assert x[0] not in ("", None)

    num_years = max(len(defaults), len(x))

    is_rate = any([i < 1.0 for i in x])

    current_policy = Policy(start_year=2013)
    current_policy.set_year(first_budget_year)
    # irates are rates for 2015, 2016, and 2017
    if cpi:
        irates = current_policy._indexing_rates_for_update(
            param_name=name, calyear=first_budget_year,
            num_years_to_expand=num_years)
    else:
        irates = [0.0] * num_years

    ans = [None] * num_years
    for i in range(num_years):
        if i < len(x):
            if is_wildcard(x[i]):
                if multi_param_idx > -1:
                    ans[i] = defaults[i][multi_param_idx]
                else:
                    ans[i] = defaults[i]

            else:
                ans[i] = x[i]

        if ans[i] is not None:
            continue
        else:
            newval = ans[i - 1] * (1.0 + irates[i - 1])
            ans[i] = newval if is_rate else int(newval)

    return ans


def expand_unless_empty(param_values, param_name, param_column_name, form,
                        new_len):
    ''' Take a list of parameters and, unless the list is empty, fill in any
    wildcards and/or expand the list to the desired number of years, using
    the proper inflation rates if necessary
    If the list is empty, return it.
    param_values: list of current values
    param_name: name of the parameter
    param_column_name: eg. _II_brk2_1 (names the sub-field)
    form: The form object that has some data for the calculation
    new_len: the new desired length of the return list
    Returns: list of length new_len, unless the empty list is passed
    '''

    if param_values == []:
        return param_values

    has_wildcards = check_wildcards(param_values)
    if len(param_values) < new_len or has_wildcards:
        # Only process wildcards and floats from this point on
        param_values = [convert_val(x) for x in param_values]
        # Discover the CPI setting for this parameter
        cpi_flag = form.discover_cpi_flag(param_name, form.cleaned_data)

        default_data = form._default_taxcalc_data[param_name]
        expnded_defaults = expand_list(default_data, new_len)

        is_multi_param = any(param_column_name.endswith("_" + suffix)
                             for suffix in ("0", "1", "2", "3"))
        if is_multi_param:
            idx = int(param_column_name[-1])
        else:
            idx = -1

        param_values = propagate_user_list(param_values,
                                           name=param_name,
                                           defaults=expnded_defaults,
                                           cpi=cpi_flag,
                                           first_budget_year=form._first_year,
                                           multi_param_idx=idx)

        param_values = [float(x) for x in param_values]

    return param_values
