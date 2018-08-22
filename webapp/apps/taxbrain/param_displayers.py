import taxcalc

from .helpers import (
    string_to_float,
    is_string)
from .param_formatters import MetaParam, parse_value


class TaxCalcField(object):
    """
    An atomic unit of data for a TaxCalcParam, which can be stored as a field
    Used for both CSV float fields (value column data) and boolean fields (cpi)
    """

    def __init__(
            self,
            id,
            label,
            values,
            param,
            first_budget_year,
            meta_param=None):
        self.id = id
        self.label = label
        self.values = values
        self.param = param

        self.values_by_year = {}
        for i, value in enumerate(values):
            year = param.start_year + i
            if meta_param is not None:
                value = parse_value(str(value), meta_param)
            self.values_by_year[year] = str(value)

        self.default_value = self.values_by_year[first_budget_year]


class TaxCalcParam(object):
    """
    A collection of TaxCalcFields that represents all configurable details
    for one of TaxCalc's Parameters
    """
    FORM_HIDDEN_PARAMS = ["widow", "separate", "dependent"]

    def __init__(self, param_id, attributes, first_budget_year,
                 use_puf_not_cps=True):
        self.__load_from_json(param_id, attributes, first_budget_year,
                              use_puf_not_cps)

    def __load_from_json(self, param_id, attributes, first_budget_year,
                         use_puf_not_cps):
        values_by_year = attributes['value']
        col_labels = attributes.get('col_label', '')

        self.tc_id = param_id
        self.nice_id = param_id[1:] if param_id[0] == '_' else param_id
        self.name = attributes['long_name']
        self.info = " ".join([
            attributes['description'],
            attributes.get('irs_ref') or "",  # sometimes this is blank
            attributes.get('notes') or ""     # sometimes this is blank
        ]).strip()

        # check that only parameters that are compatible with the current
        # data set are used
        if "compatible_data" in attributes:
            self.gray_out = not (
                (attributes["compatible_data"]["cps"] and not use_puf_not_cps)
                or (attributes["compatible_data"]["puf"] and use_puf_not_cps))
        else:
            # if compatible_data is not specified do not gray out
            self.gray_out = False

        # Pretend the start year is 2015 (instead of 2013),
        # until values for that year are provided by taxcalc
        # self.start_year = int(attributes['start_year'])
        self.start_year = first_budget_year

        self.coming_soon = False
        self.hidden = False

        # normalize single-year default lists [] to [[]]
        if not isinstance(values_by_year[0], list):
            values_by_year = [values_by_year]

        # organize defaults by column [[A1,B1],[A2,B2]] to [[A1,A2],[B1,B2]]
        values_by_col = [list(x) for x in zip(*values_by_year)]

        # Tax-Calculator converts boolean values to 1/0 via
        # np.array(bool_val, np.int8)
        # here we convert that value back to a boolean type and serialize it
        if 'boolean_value' in attributes and 'integer_value' in attributes:
            meta_param = MetaParam(
                param_name=self.nice_id,
                param_meta=attributes
            )
        else:
            meta_param = None

        if isinstance(col_labels, list):
            if col_labels == ["0kids", "1kid", "2kids", "3+kids"]:
                col_labels = ["0 Kids", "1 Kid", "2 Kids", "3+ Kids"]

        else:
            if col_labels == "NA" or col_labels == "":
                col_labels = [""]
            elif col_labels == "0kids 1kid  2kids 3+kids":
                col_labels = ["0 Kids", "1 Kid", "2 Kids", "3+ Kids"]

        # create col params
        self.col_fields = []

        if len(col_labels) == 1:
            self.col_fields.append(TaxCalcField(
                self.nice_id,
                col_labels[0],
                values_by_col[0],
                self,
                first_budget_year,
                meta_param=meta_param
            ))
        else:
            for col, label in enumerate(col_labels):
                self.col_fields.append(TaxCalcField(
                    self.nice_id + "_{0}".format(col),
                    label,
                    values_by_col[col],
                    self,
                    first_budget_year,
                    meta_param=meta_param
                ))

        # get attribute indicating whether parameter is cpi inflatable.
        self.inflatable = attributes.get("cpi_inflatable", False)

        if self.inflatable:
            cpi_flag = attributes['cpi_inflated']
            self.cpi_field = TaxCalcField(self.nice_id + "_cpi", "CPI",
                                          [cpi_flag], self, first_budget_year)

        # Get validation details
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


def parse_sub_category(field_section, budget_year, use_puf_not_cps=True):
    output = []
    free_fields = []
    for x in field_section:
        for y, z in x.items():
            section_name = dict(z).get("section_2")
            new_param = {y[y.index('_') + 1:]: TaxCalcParam(y, z, budget_year,
                                                            use_puf_not_cps)}
            if section_name:
                section = next(
                    (item for item in output if section_name in item), None)
                if not section:
                    output.append({section_name: [new_param]})
                else:
                    section[section_name].append(new_param)
            else:
                free_fields.append(field_section.pop(field_section.index(x)))
                free_fields[free_fields.index(x)] = new_param
    return output + free_fields


def parse_top_level(ordered_dict):
    output = []
    for x, y in ordered_dict.items():
        section_name = dict(y).get("section_1")
        if section_name:
            section = next(
                (item for item in output if section_name in item), None)
            if not section:
                output.append({section_name: [{x: dict(y)}]})
            else:
                section[section_name].append({x: dict(y)})
    return output


def nested_form_parameters(budget_year=2017, use_puf_not_cps=True,
                           defaults=None):
    # defaults are None unless we are testing
    if defaults is None:
        defaults_pol = taxcalc.Policy.default_data(metadata=True,
                                                   start_year=budget_year)
        defaults_behv = taxcalc.Behavior.default_data(metadata=True,
                                                      start_year=budget_year)
        defaults = dict(defaults_pol, **defaults_behv)

    groups = parse_top_level(defaults)
    for x in groups:
        for y, z in x.items():
            x[y] = parse_sub_category(z, budget_year, use_puf_not_cps)
    return groups

# Create a list of default Behavior parameters


def default_behavior(first_budget_year):
    behv_defaults = taxcalc.Behavior.default_data(metadata=True,
                                                  start_year=first_budget_year)

    default_taxcalc_params = {}
    for k, v in behv_defaults.items():
        param = TaxCalcParam(k, v, first_budget_year)
        default_taxcalc_params[param.nice_id] = param

    return default_taxcalc_params


# Create a list of default policy
def default_policy(first_budget_year, use_puf_not_cps=True):
    policy_defaults = taxcalc.Policy.default_data(metadata=True,
                                                  start_year=first_budget_year)

    default_taxcalc_params = {}
    for k, v in policy_defaults.items():
        param = TaxCalcParam(k, v, first_budget_year,
                             use_puf_not_cps=use_puf_not_cps)
        default_taxcalc_params[param.nice_id] = param

    return default_taxcalc_params


def defaults_all(first_budget_year, use_puf_not_cps=True):
    default_behv = default_behavior(first_budget_year)
    default_pol = default_policy(first_budget_year, use_puf_not_cps)
    return dict(default_behv, **default_pol)
