import pyparsing as pp
import six
import re
import ast

# Grammar for Field inputs
TRUE = pp.CaselessKeyword('true')
FALSE = pp.CaselessKeyword('false')
WILDCARD = pp.Word('*')
INT_LIT = pp.Word(pp.nums)
NEG_DASH = pp.Word('-', exact=1)
FLOAT_LIT = pp.Word(pp.nums + '.')
DEC_POINT = pp.Word('.', exact=1)
FLOAT_LIT_FULL = pp.Word(pp.nums + '.' + pp.nums)
COMMON = pp.Word(",", exact=1)
REVERSE = pp.Word("<")
VALUE = WILDCARD | NEG_DASH | FLOAT_LIT_FULL | FLOAT_LIT | INT_LIT
BOOL = WILDCARD | TRUE | FALSE


def is_safe(s):
    """
    Test if a string of comma-separated-values is "safe"
    - is the string less than 100 characters?
    - is the string boolean?
    - is the string an integer or float?
    - is the string a wildcard (*)?
    - is the string a reverse character (<)?
    If one of the tokens does not answer one of the above questions in the
    affirmative, then it is deemed "not safe"

    Returns:
        success: whether value is "safe" or not
    """
    if len(s) > 100:
        return False
    parsers = [VALUE, BOOL, REVERSE]
    tokens = s.split(',')
    success = [False] * len(tokens)
    for i, token in enumerate(tokens):
        token_strip = token.strip()
        for parser in parsers:
            try:
                parser.parseString(token_strip)
                if parser == VALUE:
                    # make sure `ast.literal_eval` can parse
                    # throws ValueError or SyntaxError on failure
                    ast.literal_eval(token_strip)
            except (pp.ParseException, ValueError, SyntaxError):
                pass
            else:
                success[i] = True
                break
    return all(success)


TRUE_REGEX = re.compile('(?i)true')
FALSE_REGEX = re.compile('(?i)false')


def is_wildcard(x):
    if isinstance(x, six.string_types):
        return x in ('*', '*') or x.strip() in ('*', '*')
    else:
        return False


def is_reverse(x):
    if isinstance(x, six.string_types):
        return x in ('<', '<') or x.strip() in ('<', '<')
    else:
        return False


def check_wildcards(x):
    if isinstance(x, list):
        return any([check_wildcards(i) for i in x])
    else:
        return is_wildcard(x)


def make_bool(x):
    """
    Find exact match for case insensitive true or false
    Returns True for True or 1
    Returns False for False or 0
    If x is wildcard then simply return x
    """
    if is_wildcard(x):
        return x
    elif x in (True, '1', '1.0', 1, 1.0):
        return True
    elif x in (False, '0', '0.0', 0, 0.0):
        return False
    elif TRUE_REGEX.match(x, endpos=4):
        return True
    elif FALSE_REGEX.match(x, endpos=5):
        return False
    else:
        # this should be caught much earlier either in model validation or in
        # form validation
        raise ValueError(
            "Expected case insensitive 'true' or 'false' but got {}".format(x)
        )


def bool_like(x):
    b = True if x == 'True' or x else False
    return b


def convert_val(x):
    if is_wildcard(x):
        return x
    if is_reverse(x):
        return x
    try:
        return float(x)
    except ValueError:
        return make_bool(x)


def is_string(x):
    return isinstance(x, str)


def string_to_float(x):
    return float(x.replace(',', ''))


INPUTS_META = ('has_errors', 'csrfmiddlewaretoken', 'start_year',
               'full_calc', 'quick_calc', 'first_year', '_state',
               'creation_date', 'id', 'job_ids', 'jobs_not_ready',
               'json_text_id', 'tax_result', 'reform_style',
               '_micro_sim_cache', 'micro_sim_id', 'raw_fields',
               'data_source', )


def json_int_key_encode(rename_dict):
    """
    Recursively rename integer value keys if they are casted to strings
    via JSON encoding

    returns: dict with new keys
    """
    if isinstance(rename_dict, dict):
        for k in list(rename_dict.keys()):
            if hasattr(k, 'isdigit') and k.isdigit():
                new_label = int(k)
            else:
                new_label = k
            rename_dict[new_label] = json_int_key_encode(rename_dict.pop(k))
    return rename_dict
