import os, tempfile, re, json, six, sys
from taxcalc import Calculator


def read_json_policy_reform_text(text_string):
    # strip out //-comments without changing line numbers
    json_str = re.sub('//.*', ' ', text_string)
    # convert JSON text into a Python dictionary
    try:
        raw_dict = json.loads(json_str)
    except ValueError as valerr:
        raise ValueError("oops")
    # check key contents of dictionary
    actual_keys = raw_dict.keys()
    for rkey in Calculator.REQUIRED_REFORM_KEYS:
        if rkey not in actual_keys:
            msg = 'key "{}" is not in policy reform file'
            raise ValueError(msg.format(rkey))
    for rkey in actual_keys:
        if rkey in Calculator.REQUIRED_ASSUMP_KEYS:
            msg = 'key "{}" should be in economic assumption file'
            raise ValueError(msg.format(rkey))
    # convert the policy dictionary in raw_dict
    rpol_dict = convert_parameter_dict(raw_dict['policy'])
    return {"user_mods": str(rpol_dict), "year": "0"}


def convert_parameter_dict(param_key_dict):
    """
    Converts specified param_key_dict into a dictionary whose primary
      keys are calendary years, and hence, is suitable as the argument to
      the Policy.implement_reform() method, or
      the Consumption.update_consumption() method, or
      the Behavior.update_behavior() method, or
      the Growdiff.update_growdiff() method.
    Specified input dictionary has string parameter primary keys and
       string years as secondary keys.
    Returned dictionary has integer years as primary keys and
       string parameters as secondary keys.
    """
    # convert year skey strings to integers and lists into np.arrays
    year_param = dict()
    for pkey, sdict in param_key_dict.items():
        if not isinstance(pkey, six.string_types):
            msg = 'pkey {} in reform is not a string'
            raise ValueError(msg.format(pkey))
        rdict = dict()
        if not isinstance(sdict, dict):
            msg = 'pkey {} in reform is not paired with a dict'
            raise ValueError(msg.format(pkey))
        for skey, val in sdict.items():
            if not isinstance(skey, six.string_types):
                msg = 'skey {} in reform is not a string'
                raise ValueError(msg.format(skey))
            else:
                year = int(skey)
            # rdict[year] = (np.array(val) if isinstance(val, list) else val)
            rdict[year] = val
        year_param[pkey] = rdict
    # convert year_param dictionary to year_key_dict dictionary
    year_key_dict = dict()
    years = set()
    for param, sdict in year_param.items():
        for year, val in sdict.items():
            if year not in years:
                years.add(year)
                year_key_dict[year] = dict()
            year_key_dict[year][param] = val
    return year_key_dict

# dir_path = os.path.dirname(os.path.realpath(__file__))
# with open(os.path.join(dir_path, "tests", "reform.json")) as f:
#     file_data = f.read()
#     data = read_json_policy_reform_text(file_data)
#
#
# def test_potato():
#     print(data)
#     assert 1
