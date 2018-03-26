from collections import defaultdict, namedtuple
import six
import json
import ast

from django.forms import NullBooleanSelect

import taxcalc

from .helpers import is_wildcard, is_reverse


MetaParam = namedtuple("MetaParam", ["param_name", "param_meta"])
CPI_WIDGET = NullBooleanSelect()

def amt_fixup(fields):
    """
    Take the regular tax captial gains parameters from the user reform
    and set them as the equivalent Alternative Minimum Tax capital
    gains parameters
    """
    cap_gains_params = ["CG_rt1", "CG_brk1_0", "CG_brk1_1",
                        "CG_brk1_2", "CG_brk1_3", "CG_brk1_cpi",
                        "CG_rt2", "CG_brk2_0", "CG_brk2_1",
                        "CG_brk2_2", "CG_brk2_3", "CG_brk2_cpi",
                        "CG_rt3"]

    for cgparam in cap_gains_params:
        if cgparam in fields:
            fields['AMT_' + cgparam] = fields[cgparam]


def parse_value(value, meta_param):
    """
    Parse the value to the type that the upstream package specification
    requires, but we let the upstream package deal with creating error messages

    returns: parsed value
    """
    # expecting a string
    assert isinstance(value, six.string_types)

    value = value.strip()

    # if value is wildcard or reverse operator, then return it
    if is_wildcard(value) or is_reverse(value):
        return value

    # get type requirements from model specification
    boolean_value = meta_param.param_meta["boolean_value"]
    if boolean_value:
        integer_value = False
    else:
        integer_value = meta_param.param_meta["integer_value"]

    # Try to parse case-insensitive True/False strings
    if value.lower() == "true":
        prepped = "True"
    elif value.lower() == "false":
        prepped = "False"
    else:
        prepped = value

    # Try to parse string and except ValueError if
    # value is not an integer, float, or boolean string
    try:
        parsed = ast.literal_eval(prepped)
    except ValueError:
        return parsed

    # Use information given to us by upstream specs to convert this value
    # into desired type or let upstream package throw error
    if boolean_value:
        if isinstance(parsed, bool):
            return parsed
        elif (isinstance(parsed, (float, int)) and
              parsed in (0, 0.0, 1, 1.0)):
            if parsed:
                return True
            else:
                return False
        else:
            # not a boolean or integer/float that is equal to 0 or 1
            # upstream package will handle the error
            return parsed
    elif integer_value:
        if isinstance(parsed, int):
            return parsed
        elif isinstance(parsed, float) and int(parsed) == parsed:
            return int(parsed)
        else:
            # rational number that cannot be casted to int without losing info
            # upstream package will handle the error
            return parsed
    else: # parsed is type float
        return float(parsed)

def parse_fields(param_dict, default_params):
    """
    Parses the raw GUI input into the correct types and maps the names to the
    appropriate default names

    returns: dictionary with parsed data
    """
    parsed = {}
    failed_lookups = []
    for k, v in param_dict.items():
        # user did not specify a value for this param
        if not v:
            continue

        # get upstream package parameter name and meta info
        try:
            meta_param = get_default_policy_param(k, default_params)
        except ParameterLookUpException:
            failed_lookups.append(k)
            continue

        values = []
        if meta_param.param_name.endswith("cpi"):
            assert len(v.split(',')) == 1
            prepped = ast.literal_eval(v)
            # raw data is stored as choices 1, 2, 3 with the following
            # mapping:
            #     '1': unknown (unknown=unspecified ==> use upstream default)
            #     '2': True
            #     '3': False
            # value_from_datadict unpacks this data:
            # https://github.com/django/django/blob/1.9/django/forms/widgets.py#L582-L589
            if prepped is 1:
                # no need to pass this to upstream model since they will be
                # filled in
                continue
            else:
                values = CPI_WIDGET.value_from_datadict(
                    {meta_param.param_name: str(prepped)},
                    None,
                    meta_param.param_name
                )
            assert isinstance(values, bool)
        else:
            for item in v.split(","):
                 values.append(parse_value(item, meta_param))
        parsed[meta_param.param_name] = values

    return parsed, failed_lookups

class ParameterLookUpException(Exception):
    pass

def get_default_policy_param(param, default_params):
    """
    Map TaxBrain field name to Tax-Calculator parameter name
    For example: STD_0 maps to _STD_single

    returns: named tuple with taxcalc param name and metadata
    """
    if '_' + param in default_params: # ex. EITC_indiv --> _EITC_indiv
        return MetaParam('_' + param, default_params['_' + param])
    param_pieces = param.split('_')
    end_piece = param_pieces[-1]
    no_suffix = '_' + '_'.join(param_pieces[:-1])
    if end_piece == 'cpi': # ex. SS_Earnings_c_cpi --> _SS_Earnings_c_cpi
        if no_suffix in default_params:
            return MetaParam('_' + param, default_params[no_suffix])
        else:
            msg = "Received unexpected parameter: {}"
            raise ParameterLookUpException(msg.format(param))
    if no_suffix in default_params: # ex. STD_0 --> _STD_single
        try:
            ix = int(end_piece)
        except ValueError:
            msg = "Parsing {}: Expected integer for index but got {}"
            raise ParameterLookUpException(msg.format(param, end_piece))
        num_columns = len(default_params[no_suffix]['col_label'])
        if ix < 0 or ix >= num_columns:
            msg = "Parsing {}: Index {} not in range ({}, {})"
            raise ParameterLookUpException(msg.format(param, ix, 0, num_columns))
        col_label = default_params[no_suffix]['col_label'][ix]
        return MetaParam(no_suffix + '_' + col_label, default_params[no_suffix])
    msg = "Received unexpected parameter: {}"
    raise ParameterLookUpException(msg.format(param))


def to_json_reform(start_year, fields):
    """
    Convert fields style dictionary to json reform style dictionary
    For example:
    start_year = 2017, cls = taxcalc.Policy
    fields = {'_CG_nodiff': [False]},
              '_FICA_ss_trt': ["*", 0.1, "*", 0.2],
              '_ID_Charity_c_cpi': True,
              '_EITC_rt_2kids': [1.0]}
    to
    reform = {'_CG_nodiff': {'2017': [False]},
              '_FICA_ss_trt': {'2020': [0.2], '2018': [0.1]},
              '_ID_Charity_c_cpi': {'2017': True},
              '_EITC_rt_2kids': {'2017': [1.0]}}

    returns: json style reform
    """
    number_reverse_operators = 1

    reform = {}
    for param in fields:
        reform[param] = {}
        if not isinstance(fields[param], list):
            assert isinstance(fields[param], bool) and param.endswith('_cpi')
            reform[param][str(start_year)] = fields[param]
            continue
        i = 0
        while i < len(fields[param]):
            if is_wildcard(fields[param][i]):
                # may need to do something here
                pass
            elif is_reverse(fields[param][i]):
                # only the first character can be a reverse char
                # and there must be a following character
                assert len(fields[param]) > 1
                # set value for parameter in start_year - 1
                assert (isinstance(fields[param][i + 1], (int, float)) or
                        isinstance(fields[param][i + 1], bool))
                reform[param][str(start_year - 1)] = \
                    [fields[param][i + 1]]

                # realign year and parameter indices
                for op in (0, number_reverse_operators + 1):
                    fields[param].pop(0)
                continue
            else:
                assert (isinstance(fields[param][i], (int, float)) or
                        isinstance(fields[param][i], bool))
                reform[param][str(start_year + i)] = \
                    [fields[param][i]]

            i += 1

    return reform


def append_errors_warnings(errors_warnings, append_func):
    """
    Appends warning/error messages to some object, append_obj, according to
    the provided function, append_func
    """
    for action in ['warnings', 'errors']:
        for param in errors_warnings[action]:
            for year in sorted(
                errors_warnings[action][param].keys(),
                key=lambda x: int(x)
            ):
                msg = errors_warnings[action][param][year]
                append_func(param, msg)


def parse_errors_warnings(errors_warnings):
    """
    Parse error messages so that they can be mapped to Taxbrain param ID. This
    allows the messages to be displayed under the field where the value is
    entered.

    returns: dictionary 'parsed' with keys: 'errors' and 'warnings'
        parsed['errors/warnings'] = {year: {tb_param_name: 'error message'}}
    """
    parsed = {'errors': defaultdict(dict), 'warnings': defaultdict(dict)}
    for action in errors_warnings:
        msgs = errors_warnings[action]
        if len(msgs) == 0:
            continue
        for msg in msgs.split('\n'):
            if len(msg) == 0: # new line
                continue
            msg_spl = msg.split()
            msg_action = msg_spl[0]
            year = msg_spl[1]
            curr_id = msg_spl[2][1:]
            msg_parse = msg_spl[2:]
            parsed[action][curr_id][year] = ' '.join([msg_action] + msg_parse +
                                                         ['for', year])

    return parsed


def read_json_reform(reform, assumptions):
    """
    Read reform and parse errors

    returns reform and assumption dictionaries that are compatible with
            taxcalc.Policy.implement_reform
            parsed warning and error messsages to be displayed on input page
            if necessary
    """
    policy_dict = taxcalc.Calculator.read_json_param_objects(
        reform,
        assumptions,
    )
    # get errors and warnings on parameters that do not cause ValueErrors
    errors_warnings = taxcalc.tbi.reform_warnings_errors(policy_dict)
    errors_warnings = parse_errors_warnings(errors_warnings)
    # separate reform and assumptions
    reform_dict = policy_dict["policy"]
    assumptions_dict = {k: v for k, v in policy_dict.items() if k != "policy"}

    return reform_dict, assumptions_dict, errors_warnings


def get_reform_from_file(request_files, reform_text=None,
                         assumptions_text=None):
    """
    Parse files from request object and collect errors_warnings

    returns reform and assumptions dictionaries that are compatible with
            taxcalc.Policy.implement_reform
            raw reform and assumptions text
            parsed warning and error messsages to be displayed on input page
            if necessary
    """
    if "docfile" in request_files:
        inmemfile_reform = request_files['docfile']
        reform_text = inmemfile_reform.read()
    if 'assumpfile' in request_files:
        inmemfile_assumption = request_files['assumpfile']
        assumptions_text = inmemfile_assumption.read()

    (reform_dict, assumptions_dict,
        errors_warnings) = read_json_reform(reform_text,
                                            assumptions_text)

    assumptions_text = assumptions_text or ""

    return (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings)


def get_reform_from_gui(start_year, taxbrain_fields=None, behavior_fields=None,
                        stored_errors=None):
    """
    Parse request and model objects and collect reforms and warnings
    This function is also called by dynamic/views.behavior_model.  In the
    future, this could be used as a generic GUI parameter parsing function.

    returns reform and assumptions dictionaries that are compatible with
            taxcalc.Policy.implement_reform
            raw reform and assumptions text
            parsed warning and error messsages to be displayed on input page
            if necessary
    """
    if taxbrain_fields is None and behavior_fields is None:
        raise ValueError("Neither taxbrain data nor behavior data was given")

    policy_dict_json = {}
    assumptions_dict_json = {}

    # prepare taxcalc params from TaxSaveInputs model
    if taxbrain_fields is not None:
        # convert GUI input to json style taxcalc reform
        policy_dict_json = to_json_reform(int(start_year),
                                          taxbrain_fields)
    if behavior_fields is not None:
        assumptions_dict_json = to_json_reform(int(start_year),
                                               behavior_fields)

    policy_dict_json = {"policy": policy_dict_json}

    policy_dict_json = json.dumps(policy_dict_json)

    assumptions_dict_json = {"behavior": assumptions_dict_json,
                             "growdiff_response": {},
                             "consumption": {},
                             "growdiff_baseline": {}}
    assumptions_dict_json = json.dumps(assumptions_dict_json)

    (reform_dict, assumptions_dict,
        errors_warnings) = read_json_reform(policy_dict_json,
                                            assumptions_dict_json)

    return (reform_dict, assumptions_dict, "", "", errors_warnings)
