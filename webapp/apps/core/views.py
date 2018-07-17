from django.shortcuts import render

# Create your views here.
def add_summary_column(table):
    import copy
    summary = copy.deepcopy(table["cols"][-1])
    summary["label"] = "Total"
    table["cols"].append(summary)
    for x in table["rows"]:
        row_total = 0
        for y in x["cells"]:
            row_total += float(y["value"])
        x["cells"].append({
            'format': {
                'decimals': 1,
                'divisor': 1000000000
            },
            'value': str(row_total),
            'year_values': {}
        })
    return table


def get_result_context(model, request, url):
    output = model.get_tax_result()
    first_year = model.first_year
    quick_calc = model.quick_calc
    created_on = model.creation_date
    if 'fiscal_tots' in output:
        # Use new key/value pairs for old data
        output['aggr_d'] = output['fiscal_tots']
        output['aggr_1'] = output['fiscal_tots']
        output['aggr_2'] = output['fiscal_tots']
        del output['fiscal_tots']

    tables = taxcalc_results_to_tables(output, first_year)
    tables["tooltips"] = {
        'distribution': DISTRIBUTION_TOOLTIP,
        'difference': DIFFERENCE_TOOLTIP,
        'payroll': PAYROLL_TOOLTIP,
        'income': INCOME_TOOLTIP,
        'base': BASE_TOOLTIP,
        'reform': REFORM_TOOLTIP,
        'bins': INCOME_BINS_TOOLTIP,
        'deciles': INCOME_DECILES_TOOLTIP,
        'fiscal_current_law': FISCAL_CURRENT_LAW,
        'fiscal_reform': FISCAL_REFORM,
        'fiscal_change': FISCAL_CHANGE,
    }

    is_from_file = not model.raw_input_fields

    if (model.json_text is not None and (model.json_text.raw_reform_text or
                                         model.json_text.raw_assumption_text)):
        reform_file_contents = model.json_text.raw_reform_text
        reform_file_contents = reform_file_contents.replace(" ", "&nbsp;")
        assump_file_contents = model.json_text.raw_assumption_text
        assump_file_contents = assump_file_contents.replace(" ", "&nbsp;")
    elif model.input_fields is not None:
        reform = to_json_reform(first_year, model.input_fields)
        reform_file_contents = json.dumps(reform, indent=4)
        assump_file_contents = '{}'
    else:
        reform_file_contents = None
        assump_file_contents = None

    is_registered = (hasattr(request, 'user') and
                     request.user.is_authenticated())

    # TODO: Fix the java script mapping problem.  There exists somewhere in
    # the taxbrain javascript code a mapping to the old table names.  As
    # soon as this is changed to accept the new table names, this code NEEDS
    # to be removed.
    tables['fiscal_change'] = add_summary_column(tables.pop('aggr_d'))
    tables['fiscal_currentlaw'] = add_summary_column(tables.pop('aggr_1'))
    tables['fiscal_reform'] = add_summary_column(tables.pop('aggr_2'))
    tables['mY_dec'] = tables.pop('dist2_xdec')
    tables['mX_dec'] = tables.pop('dist1_xdec')
    tables['df_dec'] = tables.pop('diff_itax_xdec')
    tables['pdf_dec'] = tables.pop('diff_ptax_xdec')
    tables['cdf_dec'] = tables.pop('diff_comb_xdec')
    tables['mY_bin'] = tables.pop('dist2_xbin')
    tables['mX_bin'] = tables.pop('dist1_xbin')
    tables['df_bin'] = tables.pop('diff_itax_xbin')
    tables['pdf_bin'] = tables.pop('diff_ptax_xbin')
    tables['cdf_bin'] = tables.pop('diff_comb_xbin')

    json_table = json.dumps(tables)
    # TODO: Add row labels for decile and income bin tables to the context here
    # and display these instead of hardcode in the javascript
    context = {
        'locals': locals(),
        'unique_url': url,
        'tables': json_table,
        'created_on': created_on,
        'first_year': first_year,
        'quick_calc': quick_calc,
        'is_registered': is_registered,
        'is_micro': True,
        'reform_file_contents': reform_file_contents,
        'assump_file_contents': assump_file_contents,
        'dynamic_file_contents': None,
        'is_from_file': is_from_file,
        'allow_dyn_links': not is_from_file,
        'results_type': "static"
    }
    return context


def output_detail(request, pk):
    """
    This view is the single page of diplaying a progress bar for how
    close the job is to finishing, and then it will also display the
    job results if the job is done. Finally, it will render a 'job failed'
    page if the job has failed.
    """

    try:
        url = OutputUrl.objects.get(pk=pk)
    except OutputUrl.DoesNotExist:
        raise Http404

    model = url.unique_inputs

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    context_vers_disp = {'taxcalc_version': taxcalc_vers_disp,
                         'webapp_version': webapp_vers_disp}
    if model.tax_result:
        # try to render table; if failure render not available page
        try:
            context = get_result_context(model, request, url)
        except Exception as e:
            print('Exception rendering pk', pk, e)
            traceback.print_exc()
            edit_href = '/taxbrain/edit/{}/?start_year={}'.format(
                pk,
                model.first_year or START_YEAR  # sometimes first_year is None
            )
            not_avail_context = dict(edit_href=edit_href,
                                     **context_vers_disp)
            return render(
                request,
                'taxbrain/not_avail.html',
                not_avail_context)

        context.update(context_vers_disp)
        return render(request, 'taxbrain/results.html', context)
    elif model.error_text:
        return render(request, 'taxbrain/failed.html',
                      {"error_msg": model.error_text.text})
    else:
        if not model.check_hostnames(DROPQ_WORKERS):
            print('bad hostname', model.jobs_not_ready, DROPQ_WORKERS)
            return render_to_response('taxbrain/failed.html')
        job_ids = model.job_ids
        jobs_to_check = model.jobs_not_ready
        if not jobs_to_check:
            jobs_to_check = normalize(job_ids)
        else:
            jobs_to_check = normalize(jobs_to_check)

        try:
            jobs_ready = dropq_compute.dropq_results_ready(jobs_to_check)
        except JobFailError as jfe:
            print(jfe)
            return render_to_response('taxbrain/failed.html')

        if any(j == 'FAIL' for j in jobs_ready):
            failed_jobs = [sub_id for (sub_id, job_ready)
                           in zip(jobs_to_check, jobs_ready)
                           if job_ready == 'FAIL']

            # Just need the error message from one failed job
            error_msgs = dropq_compute.dropq_get_results([failed_jobs[0]],
                                                         job_failure=True)
            if error_msgs:
                error_msg = error_msgs[0]
            else:
                error_msg = "Error: stack trace for this error is unavailable"
            val_err_idx = error_msg.rfind("Error")
            error = ErrorMessageTaxCalculator()
            error_contents = error_msg[val_err_idx:].replace(" ", "&nbsp;")
            error.text = error_contents
            error.save()
            model.error_text = error
            model.save()
            return render(request, 'taxbrain/failed.html',
                          {"error_msg": error_contents})

        if all(j == 'YES' for j in jobs_ready):
            results = dropq_compute.dropq_get_results(normalize(job_ids))
            model.tax_result = results
            model.creation_date = timezone.now()
            model.save()
            context = get_result_context(model, request, url)
            context.update(context_vers_disp)
            return render(request, 'taxbrain/results.html', context)

        else:
            jobs_not_ready = [sub_id for (sub_id, job_ready)
                              in zip(jobs_to_check, jobs_ready)
                              if job_ready == 'NO']
            jobs_not_ready = denormalize(jobs_not_ready)
            model.jobs_not_ready = jobs_not_ready
            model.save()
            if request.method == 'POST':
                # if not ready yet, insert number of minutes remaining
                exp_comp_dt = url.exp_comp_datetime
                utc_now = timezone.now()
                dt = exp_comp_dt - utc_now
                exp_num_minutes = dt.total_seconds() / 60.
                exp_num_minutes = round(exp_num_minutes, 2)
                exp_num_minutes = exp_num_minutes if exp_num_minutes > 0 else 0
                if exp_num_minutes > 0:
                    return JsonResponse({'eta': exp_num_minutes}, status=202)
                else:
                    return JsonResponse({'eta': exp_num_minutes}, status=200)

            else:
                context = {'eta': '100'}
                context.update(context_vers_disp)
                return render_to_response(
                    'taxbrain/not_ready.html',
                    context,
                    context_instance=RequestContext(request)
                )
