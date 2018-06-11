from .submit_data import PostMeta, BadPost

def save_model(post_meta):
    """
    Save user input data
    returns OutputUrl object
    """
    model = post_meta.model
    # create model for file_input case
    if model is None:
        model = TaxSaveInputs()
    model.job_ids = denormalize(post_meta.submitted_ids)
    model.json_text = post_meta.json_reform
    model.first_year = int(post_meta.start_year)
    model.data_source = post_meta.data_source
    model.quick_calc = not post_meta.do_full_calc
    model.save()

    # create OutputUrl object
    if post_meta.url is None:
        unique_url = OutputUrl()
    else:
        unique_url = post_meta.url
    if post_meta.user:
        unique_url.user = post_meta.user
    elif post_meta.request and post_meta.request.user.is_authenticated():
        current_user = User.objects.get(pk=post_meta.request.user.id)
        unique_url.user = current_user

    if unique_url.taxcalc_vers is None:
        unique_url.taxcalc_vers = TAXCALC_VERSION
    if unique_url.webapp_vers is None:
        unique_url.webapp_vers = WEBAPP_VERSION

    unique_url.unique_inputs = model
    unique_url.model_pk = model.pk
    cur_dt = datetime.datetime.utcnow()
    future_offset_seconds = ((2 + post_meta.max_q_length) * JOB_PROC_TIME_IN_SECONDS)
    future_offset = datetime.timedelta(seconds=future_offset_seconds)
    expected_completion = cur_dt + future_offset
    unique_url.exp_comp_datetime = expected_completion
    unique_url.save()

    return unique_url


def submit_reform(request, user=None, json_reform_id=None):
    """
    Parses user input data and submits reform

    returns dictionary of arguments intended to be inputs for `save_model`
    """
    fields = dict(request.GET)
    fields.update(dict(request.POST))
    fields = {k: v[0] if isinstance(v, list) else v for k, v in list(fields.items())}
    start_year = fields.get('start_year', START_YEAR)
    # TODO: migrate first_year to start_year to get rid of weird stuff like
    # this
    fields['first_year'] = fields['start_year']
    has_errors = make_bool(fields['has_errors'])

    # get files from the request object
    request_files = request.FILES

    # which file to use, front-end not yet implemented
    data_source = fields.get('data_source', 'PUF')
    if data_source == 'PUF':
        use_puf_not_cps = True
    else:
        use_puf_not_cps = False

    # declare a bunch of variables--TODO: clean this up
    no_inputs = False
    taxcalc_errors = False
    taxcalc_warnings = False
    is_valid = True
    has_parse_errors = False
    _ew = {'warnings': {}, 'errors': {}}
    errors_warnings = {'policy': _ew.copy(), 'behavior': _ew.copy()}
    reform_dict = {}
    assumptions_dict = {}
    reform_text = ""
    assumptions_text = ""
    personal_inputs = None
    model = None
    is_file = False
    submitted_ids = None
    max_q_length = None
    # Assume we do the full calculation unless we find out otherwise
    do_full_calc = False if fields.get('quick_calc') else True
    if do_full_calc and 'full_calc' in fields:
        del fields['full_calc']
    elif 'quick_calc' in fields:
        del fields['quick_calc']
    # re-submission of file for case where file-input generated warnings
    if json_reform_id:
        try:
            json_reform = JSONReformTaxCalculator.objects.get(id=int(json_reform_id))
        except Exception as e:
            msg = "ID {} is not in JSON reform database".format(json_reform_id)
            return BadPost(
                       http_response_404=HttpResponse(msg, status=400),
                       has_errors= True
                   )
        reform_dict = json.loads(json_reform.reform_text)
        assumptions_dict = json.loads(json_reform.assumption_text)
        reform_text = json_reform.raw_reform_text
        assumptions_text = json_reform.raw_assumption_text
        errors_warnings = json_reform.get_errors_warnings()

        if "docfile" in request_files or "assumpfile" in request_files:
            if "docfile" in request_files or len(reform_text) == 0:
                reform_text = None
            if "assumpfile" in request_files or len(assumptions_text) == 0:
                assumptions_text = None

            (reform_dict, assumptions_dict, reform_text, assumptions_text,
                errors_warnings) = get_reform_from_file(request_files,
                                                        reform_text,
                                                        assumptions_text)

            json_reform.reform_text = json.dumps(reform_dict)
            json_reform.assumption_text = json.dumps(assumptions_dict)
            json_reform.raw_reform_text = reform_text
            json_reform.raw_assumption_text = assumptions_text
            json_reform.errors_warnings_text = json.dumps(errors_warnings)
            json_reform.save()

            has_errors = False

    else: # fresh file upload or GUI run
        if 'docfile' in request_files:
            is_file = True
            (reform_dict, assumptions_dict, reform_text, assumptions_text,
                errors_warnings) = get_reform_from_file(request_files)
        else:
            personal_inputs = TaxBrainForm(start_year, use_puf_not_cps, fields)
            # If an attempt is made to post data we don't accept
            # raise a 400
            if personal_inputs.non_field_errors():
                return BadPost(
                           http_response_404=HttpResponse("Bad Input!", status=400),
                           has_errors= True
                       )
            is_valid = personal_inputs.is_valid()
            if is_valid:
                model = personal_inputs.save(commit=False)
                model.set_fields()
                model.save()
                (reform_dict, assumptions_dict, reform_text, assumptions_text,
                    errors_warnings) = model.get_model_specs()
        json_reform = JSONReformTaxCalculator(
            reform_text=json.dumps(reform_dict),
            assumption_text=json.dumps(assumptions_dict),
            raw_reform_text=reform_text,
            raw_assumption_text=assumptions_text,
            errors_warnings_text=json.dumps(errors_warnings)
        )
        json_reform.save()

    if reform_dict == {}:
        no_inputs = True
    # TODO: account for errors
    # 5 cases:
    #   0. no warning/error messages --> run model
    #   1. has seen warning/error messages and now there are no errors -- > run model
    #   2. has not seen warning/error messages --> show warning/error messages
    #   3. has seen warning/error messages and there are still error messages
    #        --> show warning/error messages again
    #   4. no user input --> do not run model

    # We need to stop on both! File uploads should stop if there are 'behavior'
    # or 'policy' errors
    warn_msgs = any([len(errors_warnings[project]['warnings']) > 0
                      for project in ['policy', 'behavior']])
    error_msgs = any([len(errors_warnings[project]['errors']) > 0
                      for project in ['policy', 'behavior']])
    stop_errors = no_inputs or not is_valid or error_msgs
    stop_submission = stop_errors or (not has_errors and warn_msgs)
    if stop_submission:
        taxcalc_errors = True if error_msgs else False
        taxcalc_warnings = True if warn_msgs else False
        if personal_inputs is not None:
            # ensure that parameters causing the warnings are shown on page
            # with warnings/errors
            personal_inputs = TaxBrainForm(
                start_year,
                use_puf_not_cps,
                initial=json.loads(personal_inputs.data['raw_input_fields'])
            )
            # TODO: parse warnings for file_input
            # only handle GUI errors for now
            if ((taxcalc_errors or taxcalc_warnings)
                    and personal_inputs is not None):
                # we are only concerned with adding *static* reform errors to
                # the *static* reform page.
                append_errors_warnings(
                    errors_warnings['policy'],
                    lambda param, msg: personal_inputs.add_error(param, msg)
                )
            has_parse_errors = any(['Unrecognize value' in e[0]
                                    for e in list(personal_inputs.errors.values())])
            if no_inputs:
                personal_inputs.add_error(
                    None,
                    "Please specify a tax-law change before submitting."
                )
            if taxcalc_warnings or taxcalc_errors:
                personal_inputs.add_error(None, OUT_OF_RANGE_ERROR_MSG)
            if has_parse_errors:
                msg = ("Some fields have unrecognized values. Enter comma "
                       "separated values for each input.")
                personal_inputs.add_error(None, msg)
    else:
        log_ip(request)
        user_mods = dict({'policy': reform_dict}, **assumptions_dict)
        data = {'user_mods': json.dumps(user_mods),
                'first_budget_year': int(start_year),
                'start_budget_year': 0,
                'use_puf_not_cps': use_puf_not_cps}
        if do_full_calc:
            data['num_budget_years'] = NUM_BUDGET_YEARS
            submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(
                data
            )
        else:
            data['num_budget_years'] = NUM_BUDGET_YEARS_QUICK
            submitted_ids, max_q_length = dropq_compute.submit_dropq_small_calculation(
                data
            )

    return PostMeta(
               request=request,
               personal_inputs=personal_inputs,
               json_reform=json_reform,
               model=model,
               stop_submission=stop_submission,
               has_errors=any([taxcalc_errors, taxcalc_warnings,
                               no_inputs, not is_valid]),
               errors_warnings=errors_warnings,
               start_year=start_year,
               data_source=data_source,
               do_full_calc=do_full_calc,
               is_file=is_file,
               reform_dict=reform_dict,
               assumptions_dict=assumptions_dict,
               reform_text=reform_text,
               assumptions_text=assumptions_text,
               submitted_ids=submitted_ids,
               max_q_length=max_q_length,
               user=user,
               url=None
           )


def process_reform(request, user=None, **kwargs):
    """
    Submits TaxBrain reforms.  This handles data from the GUI interface
    and the file input interface.  With some tweaks this model could be used
    to submit reforms for all PolicyBrain models

    returns OutputUrl object with parsed user input and warning/error messages
            if necessary
            boolean variable indicating whether this reform has errors or not

    """
    post_meta = submit_reform(request, user=user, **kwargs)
    if isinstance(post_meta, BadPost):
        return None, post_meta

    if post_meta.stop_submission:
        return None, post_meta#(args['personal_inputs'], args['json_reform'], args['has_errors'],
                #errors_warnings)
    else:
        url = save_model(post_meta)
        return url, post_meta
