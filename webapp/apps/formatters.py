import os, tempfile, re, json, six, sys


def format_dynamic_params(params):
    behavior_params = {}
    behavior_params["behavior"] = {str(params["first_year"]): {"_" + k:v for k, v in params.items() if k.startswith("BE")}}
    for key in ("growdiff_response", "consumption", "growdiff_baseline"):
        behavior_params[key] = {}
    return behavior_params

def get_version(url_obj, attr_name, current_version):
    """
    get formatted python version of library for diplay on web page
    """
    # need to chop off the commit reference on older runs
    vers_disp = (getattr(url_obj, attr_name) 
                 if getattr(url_obj, attr_name) else current_version)
    # only recently start storing webapp version. for older runs display
    # the current version. an alternative is to display the first stable
    # version if url.webapp_version is None
    if len(vers_disp.split('.')) > 3:
        vers_disp = '.'.join(vers_disp.split('.')[:-1])

    return vers_disp
