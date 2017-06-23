import os, tempfile, re, json, six, sys
from taxcalc import Calculator


def format_dynamic_params(params):
    behavior_params = {}
    behavior_params["behavior"] = {str(params["first_year"]): {"_" + k:v for k, v in params.items() if k.startswith("BE")}}
    for key in ("growdiff_response", "consumption", "growdiff_baseline"):
        behavior_params[key] = {}
    return behavior_params
