from collections import namedtuple
import numbers
import os
import pandas as pd
import json
import string
import sys
import time
import six

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys

from ..taxbrain.helpers import (make_bool, convert_val,
                                is_wildcard, int_to_nth,
                                is_number, is_string,
                                string_to_float, string_to_float_array,
                                same_version, arrange_totals_by_row,
                                round_gt_one_to_nearest_int, expand_1D,
                                expand_2D, expand_list, leave_name_in,
                                TaxCalcField)

import btax
from btax.util import read_from_egg

PYTHON_MAJOR_VERSION = sys.version_info.major

BTAX_BITR = ['btax_betr_corp',
             'btax_betr_pass',
             'btax_betr_entity_Switch']
BTAX_DEPREC = ['btax_depr_allyr', 'btax_depr_3yr', 'btax_depr_5yr',
               'btax_depr_7yr', 'btax_depr_10yr',
               'btax_depr_15yr','btax_depr_20yr', 'btax_depr_25yr',
               'btax_depr_27_5yr', 'btax_depr_39yr']
BTAX_OTHER = ['btax_other_hair', 'btax_other_corpeq',
              'btax_other_proptx','btax_other_invest']
BTAX_ECON = ['btax_econ_nomint', 'btax_econ_inflat',]


BTAX_VERSION_INFO = btax._version.get_versions()
BTAX_VERSION = ".".join([BTAX_VERSION_INFO['version'], BTAX_VERSION_INFO['full-revisionid'][:6]])

# Row labels, in order, including minor headings like "Durable goods"
BTAX_TABLE_ASSET_ORDER = ("Equipment", "Mainframes", "PCs", "DASDs", "Printers", "Terminals", "Tape drives", "Storage devices", "System integrators", "Communications", "Nonelectro medical instruments", "Electro medical instruments", "Nonmedical instruments", "Photocopy and related equipment", "Office and accounting equipment", "Nuclear fuel", "Other fabricated metals", "Steam engines", "Internal combustion engines", "Metalworking machinery", "Special industrial machinery", "General industrial equipment", "Electric transmission and distribution", "Light trucks (including utility vehicles)", "Other trucks, buses and truck trailers", "Autos", "Aircraft", "Ships and boats", "Railroad equipment", "Household furniture", "Other furniture", "Other agricultural machinery", "Farm tractors", "Other construction machinery", "Construction tractors", "Mining and oilfield machinery", "Service industry machinery", "Household appliances", "Other electrical", "Other", "Structures", "Office", "Hospitals", "Special care", "Medical buildings", "Multimerchandise shopping", "Food and beverage establishments", "Warehouses", "Mobile structures", "Other commercial", "Manufacturing", "Electric", "Wind and solar", "Gas", "Petroleum pipelines", "Communication", "Petroleum and natural gas", "Mining", "Educational and vocational", "Lodging", "Amusement and recreation", "Air transportation", "Other transportation", "Other railroad", "Track replacement", "Local transit structures", "Other land transportation", "Farm", "Water supply", "Sewage and waste disposal", "Public safety", "Highway and conservation and development", "Inventories", "Land")
BTAX_TABLE_INDUSTRY_ORDER = ("Agriculture, forestry, fishing, and hunting", "Farms", "Forestry, fishing, and related activities", "Mining", "Oil and gas extraction", "Mining, except oil and gas", "Support activities for mining", "Utilities", "Construction", "Manufacturing", "Durable goods", "Wood products", "Nonmetallic mineral products", "Primary metals", "Fabricated metal products", "Machinery", "Computer and electronic products", "Electrical equipment, appliances, and components", "Motor vehicles, bodies and trailers, and parts", "Other transportation equipment", "Furniture and related products", "Miscellaneous manufacturing", "Nondurable goods", "Food, beverage, and tobacco products", "Textile mills and textile product mills", "Apparel and leather and allied products", "Paper products", "Printing and related support activities", "Petroleum and coal products", "Chemical products", "Plastics and rubber products", "Wholesale trade", "Retail trade", "Transportation and warehousing", "Air transportation", "Railroad transportation", "Water transportation", "Truck transportation", "Transit and ground passenger transportation", "Pipeline transportation", "Other transportation and support activities", "Warehousing and storage", "Information", "Publishing industries (including software)", "Motion picture and sound recording industries", "Broadcasting and telecommunications", "Information and data processing services", "Finance and insurance", "Credit intermediation and related activities", "Securities, commodity contracts, and investments", "Insurance carriers and related activities", "Funds, trusts, and other financial vehicles", "Real estate and rental and leasing", "Real estate", "Rental and leasing services and lessors of intangible assets", "Professional, scientific, and technical services", "Legal services", "Computer systems design and related services", "Miscellaneous professional, scientific, and technical services", "Management of companies and enterprises", "Administrative and waste management services", "Administrative and support services", "Waste management and remediation services", "Educational services", "Health care and social assistance", "Ambulatory health care services", "Hospitals", "Nursing and residential care facilities", "Social assistance", "Arts, entertainment, and recreation", "Performing arts, spectator sports, museums, and related activities", "Amusements, gambling, and recreation industries", "Accommodation and food services", "Accommodation", "Food services and drinking places", "Other services, except government")
# If any minor headings are needed, such as "Durable goods", put them in "breaks" below
BTAX_TABLE_BREAKS = {'industry': ['Durable goods', 'Nondurable goods'], 'asset': []}
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
    def __init__(self, param_id, attributes):
        self.__load_from_json(param_id, attributes)

    def __load_from_json(self, param_id, attributes):
        # TODO does /ccc need to handle
        # budget year /start year logic
        # as in /taxbrain. If so, see
        # TaxCalcParam for changes to
        # make here
        self.start_year = first_budget_year = 2015

        values_by_year = attributes['value']
        col_labels = attributes['col_label']

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

        self.col_fields.append(TaxCalcField(
            self.nice_id,
            attributes['description'],
            values_by_col[0],
            self,
            first_budget_year
        ))

        # we assume we can CPI inflate if first value isn't a ratio
        first_value = self.col_fields[0].values[0]

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


def get_btax_defaults():
    from btax import DEFAULTS
    defaults = dict(DEFAULTS)
    # Set Bogus default for now
    defaults['btax_betr_pass']['value'] = [0.0]
    for k,v in defaults.items():
        v['col_label'] = ['']
    BTAX_DEFAULTS = {}

    for k in (BTAX_BITR + BTAX_OTHER + BTAX_ECON):
        param = BTaxParam(k,defaults[k])
        BTAX_DEFAULTS[param.nice_id] = param
    for k in BTAX_DEPREC:
        fields = ['{}_{}_Switch'.format(k, tag)
                     for tag in ('gds', 'ads',  'tax')]
        for field in fields:
            param = BTaxParam(field, defaults[field])
            BTAX_DEFAULTS[param.nice_id] = param
        for field in ['{}_{}'.format(k, 'exp')]:
            param = BTaxParam(field, defaults[field])
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
    hover_notes['economic_note'] = defaults['btax_depr_hover_tax_Switch']['notes']
    hover_notes['bonus_note'] = defaults['btax_depr_hover_exp']['notes']
    return hover_notes


def group_args_to_btax_depr(btax_default_params, asset_yr_str):
    depr_field_order = ('gds', 'ads', 'exp', 'tax')
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
            td_style_class = 'table-check-all-item'
            tr_style_class = 'tr-check-all'
        else:
            td_style_class = ''
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

def btax_results_to_tables(results, first_budget_year):
    """
    Take various results from i.e. mY_dec, mX_bin, df_dec, etc
    Return organized and labeled table results for display
    """
    asset_col_meta = dict(btax.parameters.DEFAULT_ASSET_COLS)
    industry_col_meta = dict(btax.parameters.DEFAULT_INDUSTRY_COLS)
    r = results[0]
    tables_to_process = {k: v for k, v in r.items()
                         if k.startswith(('asset_', 'industry_'))}
    row_grouping = r.get('row_grouping', {})
    tables = {}
    for upper_key, table_data0 in tables_to_process.items():
        if not upper_key in tables:
            tables[upper_key] = {}
        for table_id, table_data in table_data0.items():
            col_labels = table_data[0]
            row_labels = [_[0] for _ in table_data[1:]]
            table = {
                'col_labels': col_labels,
                'cols': [],
                'label': table_id,
                'rows': [],
            }
            is_asset = 'asset_' in upper_key
            meta = asset_col_meta if is_asset else industry_col_meta
            for col_key, label in enumerate(col_labels):
                col_dict = [v for k, v in meta.items()
                            if v['col_label'] == label][0]
                table['cols'].append({
                    'label': label,
                    'divisor': v.get('divisor', 1),
                    'units': '',
                    'decimals': v.get('decimals', 0),
                })

            col_count = len(col_labels)
            group_data = row_grouping['asset' if is_asset else 'industry']
            spaces = (u'\xa0', u'\u00a0', u' ')
            keys = tuple(group_data)
            ks = [[char for char in _ if char not in spaces]
                   for _ in group_data]
            if is_asset:
                row_order = BTAX_TABLE_ASSET_ORDER
            else:
                row_order = BTAX_TABLE_INDUSTRY_ORDER
            breaks = BTAX_TABLE_BREAKS['asset' if is_asset else 'industry']
            def closest_spell(a):
                '''Ignore spaces, including unicode-encoded spaces
                   for comparison'''
                k = [k for k in ks
                     if a and [char for char in a if char not in spaces] == k][0]
                return keys[ks.index(k)]
            befores = []
            for b in breaks:
                before = [r1 for r1, r2 in zip(row_order[:-1], row_order[1:])
                          if r2 == b][0]
                befores.append(before)
            row_order = [r for r in row_order if r not in breaks]
            for idx, row_label in enumerate(row_order, 1):
                if row_label in befores:
                    lab = breaks[befores.index(row_label)]
                    extra_row = {'label': lab,
                                 'summary_c': 'breakline',
                                 'summary_nc': 'breakline',
                                 'major_grouping': lab,
                                 'cells': []}
                else:
                    extra_row = None
                row_key = closest_spell(row_label)
                group = group_data[row_key]
                row = {
                    'label': row_label,
                    'cells': [],
                    'major_grouping': group['major_grouping'],
                    'summary_c': '{:.03f}'.format(group['summary_c']),
                    'summary_nc': '{:.03f}'.format(group['summary_nc']),
                }

                for col_key in range(0, col_count):
                    value = table_data[idx][col_key+1]
                    cell = {
                        'format': {
                            'divisor': table['cols'][col_key]['divisor'],
                            'decimals': table['cols'][col_key]['decimals'],
                        },
                        'value': value,
                    }

                    cell['value'] = value
                    row['cells'].append(cell)
                table['rows'].append(row)
                if extra_row:
                    table['rows'].append(extra_row)

            tables[upper_key][table_id] = table
    tables['result_years'] = [2015]
    return tables
