from collections import namedtuple
import datetime
import json

from django.utils import timezone
from ipware.ip import get_real_ip
from django.http import HttpResponse
from django.contrib.auth.models import User

from ..taxbrain.models import TaxBrainRun, TaxSaveInputs
from ..core.compute import NUM_BUDGET_YEARS, NUM_BUDGET_YEARS_QUICK
from .forms import TaxBrainForm
from .helpers import make_bool, json_int_key_encode
from .param_formatters import get_reform_from_file, append_errors_warnings
from ..constants import (START_YEAR, OUT_OF_RANGE_ERROR_MSG,
                         WEBAPP_VERSION, TAXCALC_VERSION)

JOB_PROC_TIME_IN_SECONDS = 35

PostMeta = namedtuple(
    'PostMeta',
    ['request',
     'personal_inputs',
     'model',
     'stop_submission',
     'has_errors',
     'errors_warnings',
     'start_year',
     'data_source',
     'do_full_calc',
     'reform_parameters',
     'assumption_parameters',
     'reform_inputs_file',
     'assumption_inputs_file',
     'submitted_id',
     'max_q_length',
     'user',
     'url',
     'years_n']
)

BadPost = namedtuple('BadPost', ['http_response_404', 'has_errors'])


def process_reform(request, dropq_compute, user=None, **kwargs):
    """
    Submits TaxBrain reforms.  This handles data from the GUI interface
    and the file input interface.  With some tweaks this model could be used
    to submit reforms for all PolicyBrain models

    returns:
    - url: OutputUrl object with parsed user input and warning/error
        messages if necessary
    - post_meta: namedtuple containing data relevant to the parameter
        submission
    """
    post_meta = submit_reform(request, dropq_compute, user=user, **kwargs)
    if isinstance(post_meta, BadPost) or post_meta.stop_submission:
        return None, post_meta
        # (args['personal_inputs'], args['json_reform'], args['has_errors'],
        #  errors_warnings)
    else:
        url = save_model(post_meta)
        return url, post_meta


def save_model(post_meta):
    """
    Save user input data
    returns OutputUrl object
    """
    model = post_meta.model
    # create model for file_input case
    if model is None:
        model = TaxSaveInputs()
    model.upstream_parameters.update({
        'reform': post_meta.reform_parameters,
        'assumption': post_meta.assumption_parameters})
    model.inputs_file.update({
        'reform': post_meta.reform_inputs_file,
        'assumption': post_meta.assumption_inputs_file})
    model.first_year = int(post_meta.start_year)
    model.data_source = post_meta.data_source
    model.quick_calc = not post_meta.do_full_calc
    model.years_n = ",".join(str(i) for i in post_meta.years_n)
    model.save()

    # create OutputUrl object
    if post_meta.url is None:
        unique_url = TaxBrainRun()
    else:
        unique_url = post_meta.url
    unique_url.job_id = post_meta.submitted_id
    unique_url.inputs = model
    unique_url.save()

    if post_meta.user:
        unique_url.user = post_meta.user
    elif post_meta.request and post_meta.request.user.is_authenticated():
        current_user = User.objects.get(pk=post_meta.request.user.id)
        unique_url.user = current_user

    if unique_url.upstream_vers is None:
        unique_url.upstream_vers = TAXCALC_VERSION
    if unique_url.webapp_vers is None:
        unique_url.webapp_vers = WEBAPP_VERSION

    cur_dt = timezone.now()
    future_offset_seconds = ((2 + post_meta.max_q_length) *
                             JOB_PROC_TIME_IN_SECONDS)
    future_offset = datetime.timedelta(seconds=future_offset_seconds)
    expected_completion = cur_dt + future_offset
    unique_url.exp_comp_datetime = expected_completion
    unique_url.save()

    return unique_url


def submit_reform(request, dropq_compute, user=None, inputs_id=None):
    """
    Parses user input data and submits reform

    returns dictionary of arguments intended to be inputs for `save_model`
    """
    fields = dict(request.GET)
    fields.update(dict(request.POST))
    fields = {k: v[0] if isinstance(v, list) else v
              for k, v in list(fields.items())}
    start_year = fields.get('start_year', START_YEAR)
    # TODO: migrate first_year to start_year to get rid of weird stuff like
    # this
    fields['first_year'] = fields['start_year']
    has_errors = make_bool(fields['has_errors'])

    # get files from the request object
    request_files = request.FILES

    # which file to use, front-end not yet implemented
    data_source = fields.get('data_source', 'PUF')
    use_puf_not_cps = (data_source == 'PUF')

    # declare a bunch of variables--TODO: clean this up
    taxcalc_errors = False
    taxcalc_warnings = False
    is_valid = True
    has_parse_errors = False
    _ew = {'warnings': {}, 'errors': {}}
    errors_warnings = {'policy': _ew.copy(), 'behavior': _ew.copy()}
    reform_parameters = {}
    assumption_parameters = {}
    reform_inputs_file = ""
    assumption_inputs_file = ""
    personal_inputs = None
    model = None
    submitted_id = None
    max_q_length = None
    # Assume we do the full calculation unless we find out otherwise
    do_full_calc = False if fields.get('quick_calc') else True
    if do_full_calc and 'full_calc' in fields:
        del fields['full_calc']
    elif 'quick_calc' in fields:
        del fields['quick_calc']

    # re-submission of file for case where file-input generated warnings
    if inputs_id:
        try:
            model = TaxSaveInputs.objects.get(id=int(inputs_id))
        except Exception:
            msg = "ID {} is not in inputs database".format(inputs_id)
            return BadPost(
                http_response_404=HttpResponse(msg, status=400),
                has_errors=True
            )
        reform_parameters = json_int_key_encode(
            model.upstream_parameters['reform'])
        assumption_parameters = json_int_key_encode(
            model.upstream_parameters['assumption'])
        reform_inputs_file = model.inputs_file['reform']
        assumption_inputs_file = model.inputs_file['assumption']
        errors_warnings = model.errors_warnings_text

        if "docfile" in request_files or "assumpfile" in request_files:
            if "docfile" in request_files or len(reform_inputs_file) == 0:
                reform_inputs_file = None
            if ("assumpfile" in request_files or
                    len(assumption_inputs_file) == 0):
                assumption_inputs_file = None

            (reform_parameters, assumption_parameters, reform_inputs_file,
                assumption_inputs_file,
                errors_warnings) = get_reform_from_file(request_files,
                                                        reform_inputs_file,
                                                        assumption_inputs_file)

            model.upstream_parameters.update({
                'reform': reform_parameters,
                'assumption': assumption_parameters})
            model.inputs_file.update({
                'reform': reform_inputs_file,
                'assumption': assumption_inputs_file})
            model.errors_warnings_text = errors_warnings
            model.save()

            has_errors = False

    else:  # fresh file upload or GUI run
        if 'docfile' in request_files:
            model = TaxSaveInputs()
            (reform_parameters, assumption_parameters, reform_inputs_file,
                assumption_inputs_file,
                errors_warnings) = get_reform_from_file(request_files)
        else:
            personal_inputs = TaxBrainForm(start_year, use_puf_not_cps, fields)
            # If an attempt is made to post data we don't accept
            # raise a 400
            if personal_inputs.non_field_errors():
                return BadPost(
                    http_response_404=HttpResponse(
                        "Bad Input!", status=400
                    ),
                    has_errors=True
                )
            is_valid = personal_inputs.is_valid()
            if is_valid:
                model = personal_inputs.save(commit=False)
                model.set_fields()
                model.save()
                (reform_parameters, assumption_parameters, reform_inputs_file,
                    assumption_inputs_file,
                    errors_warnings) = model.get_model_specs()

        if model:
            model.upstream_parameters.update({
                'reform': reform_parameters,
                'assumption': assumption_parameters})
            model.inputs_file.update({
                'reform': reform_inputs_file,
                'assumption': assumption_inputs_file})
            model.errors_warnings_text = errors_warnings
            model.save()

    # TODO: account for errors
    # 4 cases:
    #   0. no warning/error messages --> run model
    #   1. has seen warning/error messages and now there are no errors
    #        --> run model
    #   2. has not seen warning/error messages --> show warning/error messages
    #   3. has seen warning/error messages and there are still error messages
    #        --> show warning/error messages again

    # We need to stop on both! File uploads should stop if there are 'behavior'
    # or 'policy' errors
    warn_msgs = any(len(errors_warnings[project]['warnings']) > 0
                    for project in ['policy', 'behavior'])
    error_msgs = any(len(errors_warnings[project]['errors']) > 0
                     for project in ['policy', 'behavior'])
    stop_errors = not is_valid or error_msgs
    stop_submission = stop_errors or (not has_errors and warn_msgs)

    years_n = (list(range(NUM_BUDGET_YEARS)) if do_full_calc
               else list(range(NUM_BUDGET_YEARS_QUICK)))

    if stop_submission:
        taxcalc_errors = bool(error_msgs)
        taxcalc_warnings = bool(warn_msgs)
        if personal_inputs is not None:
            # ensure that parameters causing the warnings are shown on page
            # with warnings/errors
            personal_inputs = TaxBrainForm(
                start_year,
                use_puf_not_cps,
                initial=json.loads(
                    personal_inputs.data['raw_gui_field_inputs'])
            )
            # TODO: parse warnings for file_input
            # only handle GUI errors for now
            if ((taxcalc_errors or taxcalc_warnings) and
                    personal_inputs is not None):
                # we are only concerned with adding *static* reform errors to
                # the *static* reform page.
                append_errors_warnings(
                    errors_warnings['policy'],
                    lambda param, msg: personal_inputs.add_error(param, msg)
                )
            has_parse_errors = any('Unrecognize value' in e[0]
                                   for e
                                   in list(personal_inputs.errors.values()))
            if taxcalc_warnings or taxcalc_errors:
                personal_inputs.add_error(None, OUT_OF_RANGE_ERROR_MSG)
            if has_parse_errors:
                msg = ("Some fields have unrecognized values. Enter comma "
                       "separated values for each input.")
                personal_inputs.add_error(None, msg)
    else:
        log_ip(request)
        user_mods = {'policy': reform_parameters, **assumption_parameters}
        data = {'user_mods': user_mods,
                'first_budget_year': int(start_year),
                'use_puf_not_cps': use_puf_not_cps}
        data_list = [dict(year=i, **data) for i in years_n]
        if do_full_calc:
            submitted_id, max_q_length = (
                dropq_compute.submit_calculation(data_list))
        else:
            submitted_id, max_q_length = (
                dropq_compute.submit_quick_calculation(data_list))

    return PostMeta(
        request=request,
        personal_inputs=personal_inputs,
        model=model,
        stop_submission=stop_submission,
        has_errors=any([taxcalc_errors, taxcalc_warnings,
                        not is_valid]),
        errors_warnings=errors_warnings,
        start_year=start_year,
        data_source=data_source,
        do_full_calc=do_full_calc,
        reform_parameters=reform_parameters,
        assumption_parameters=assumption_parameters,
        reform_inputs_file=reform_inputs_file,
        assumption_inputs_file=assumption_inputs_file,
        submitted_id=submitted_id,
        max_q_length=max_q_length,
        user=user,
        url=None,
        years_n=years_n
    )


def log_ip(request):
    """
    Attempt to get the IP address of this request and log it
    """
    ip = get_real_ip(request)
    if ip is not None:
        # we have a real, public ip address for user
        print("BEGIN DROPQ WORK FROM: ", ip)
    else:
        # we don't have a real, public ip address for user
        print("BEGIN DROPQ WORK FROM: unknown IP")
