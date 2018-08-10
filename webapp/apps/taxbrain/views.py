import os


from mock import Mock
import sys

from urllib.parse import urlparse, parse_qs

from django.shortcuts import render, redirect, get_object_or_404

from .forms import TaxBrainForm
from .helpers import (taxcalc_results_to_tables, format_csv,
                      json_int_key_encode)
from .param_displayers import nested_form_parameters
from ..core.compute import Compute, JobFailError, NUM_BUDGET_YEARS
from ..taxbrain.models import TaxBrainRun
from ..core.views import CoreRunDetailView, CoreRunDownloadView
from ..core.models import Tag, TagOption

from ..constants import (DISTRIBUTION_TOOLTIP, DIFFERENCE_TOOLTIP,
                         PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                         REFORM_TOOLTIP, FISCAL_CURRENT_LAW, FISCAL_REFORM,
                         FISCAL_CHANGE, INCOME_BINS_TOOLTIP,
                         INCOME_DECILES_TOOLTIP, START_YEAR, START_YEARS,
                         DATA_SOURCES, DEFAULT_SOURCE, OUT_OF_RANGE_ERROR_MSG,
                         WEBAPP_VERSION, TAXCALC_VERSION)

from ..formatters import get_version
from .param_formatters import append_errors_warnings
from .submit_data import PostMeta, BadPost, process_reform, save_model, log_ip

# Mock some module for imports because we can't fit them on Heroku slugs
MOCK_MODULES = ['matplotlib', 'matplotlib.pyplot', 'mpl_toolkits',
                'mpl_toolkits.mplot3d']
ENABLE_QUICK_CALC = bool(os.environ.get('ENABLE_QUICK_CALC', ''))
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

dropq_compute = Compute()

class TaxBrainRunDetailView(CoreRunDetailView):
    model = TaxBrainRun

    result_header = "Static Results"

    tags = [
        Tag(key="table_type",
            values=[
                TagOption(
                    value="dist",
                    title="Distribution Table",
                    tooltip=DISTRIBUTION_TOOLTIP,
                    children=[
                        Tag(key="law",
                            values=[
                                TagOption(
                                    value="current",
                                    title="Current Law",
                                    tooltip=BASE_TOOLTIP),
                                TagOption(
                                    value="reform",
                                    title="Reform",
                                    tooltip=REFORM_TOOLTIP)])]),
                TagOption(
                    value="diff",
                    title="Difference Table",
                    tooltip=DIFFERENCE_TOOLTIP,
                    children=[
                        Tag(key="tax_type",
                            values=[
                                TagOption(
                                    value="payroll",
                                    title="Payroll Tax",
                                    tooltip=PAYROLL_TOOLTIP),
                                TagOption(
                                    value="ind_income",
                                    title="Income Tax",
                                    tooltip=INCOME_TOOLTIP),
                                TagOption(
                                    value="combined",
                                    title="Combined",
                                    tooltip="")  # TODO
                            ])])]),
        Tag(key="grouping",
            values=[
                TagOption(
                    value="bins",
                    title="Income Bins",
                    tooltip=INCOME_BINS_TOOLTIP),
                TagOption(
                    value="deciles",
                    title="Income Deciles",
                    tooltip=INCOME_DECILES_TOOLTIP)
            ])]
    aggr_tags = [
        Tag(key="law",
            values=[
                TagOption(
                    value="current",
                    title="Current Law"),
                TagOption(
                    value="reform",
                    title="Reform"),
                TagOption(
                    value="change",
                    title="Change")
            ])]

    def has_link_to_dyn(self):
        return not self.is_from_file()


class TaxBrainRunDownloadView(CoreRunDownloadView):
    model = TaxBrainRun


def file_input(request):
    """
    Receive request from file input interface and returns parsed data or an
    input form
    """
    form_id = request.POST.get('form_id', None)
    if form_id == 'None':
        form_id = None

    start_year = START_YEAR
    data_source = DEFAULT_SOURCE
    errors = []
    has_errors = False
    print('files', request.FILES)
    if request.method == 'POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        # save start_year
        start_year = (request.GET.get('start_year', None) or
                      request.POST.get('start_year', None))
        assert start_year is not None
        data_source = (request.GET.get('data_source', None) or
                       request.POST.get('start_year', None))
        assert data_source is not None

        # File is not submitted
        if 'docfile' not in dict(request.FILES) and form_id is None:
            errors = ["Please specify a tax-law change before submitting."]
            inputs = None
        else:
            obj, post_meta = process_reform(request, dropq_compute,
                                            inputs_id=form_id)
            if isinstance(post_meta, BadPost):
                return post_meta.http_response_404
            else:
                unique_url = obj

            if post_meta.stop_submission:
                errors_warnings = post_meta.errors_warnings
                inputs = post_meta.model
                has_errors = post_meta.has_errors
                errors.append(OUT_OF_RANGE_ERROR_MSG)
                for project in ['policy', 'behavior']:
                    append_errors_warnings(
                        errors_warnings[project],
                        lambda _, msg: errors.append(msg)
                    )
            else:
                return redirect(unique_url)
    else:
        # Probably a GET request, load a default form
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        if ('data_source' in params and
                params['data_source'][0] in DATA_SOURCES):
            data_source = params['data_source'][0]

        inputs = None

    init_context = {
        'form_id': inputs.id if inputs is not None else None,
        'errors': errors,
        'has_errors': has_errors,
        'upstream_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'params': None,
        'start_years': START_YEARS,
        'start_year': start_year,
        'data_sources': DATA_SOURCES,
        'data_source': data_source,
        'enable_quick_calc': ENABLE_QUICK_CALC,
        'input_type': "file"
    }

    return render(request, 'taxbrain/input_file.html', init_context)


def personal_results(request):
    """
    Receive data from GUI interface and returns parsed data or default data if
    get request
    """
    start_year = START_YEAR
    has_errors = False
    data_source = DEFAULT_SOURCE
    if request.method == 'POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        obj, post_meta = process_reform(request, dropq_compute)
        # case where validation failed in forms.TaxBrainForm
        # TODO: assert HttpResponse status is 404
        if isinstance(post_meta, BadPost):
            return post_meta.http_response_404

        # No errors--submit to model
        if not post_meta.stop_submission:
            return redirect(obj)
        # Errors from taxcalc.tbi.reform_warnings_errors
        else:
            personal_inputs = post_meta.personal_inputs
            start_year = post_meta.start_year
            data_source = post_meta.data_source
            use_puf_not_cps = (data_source == 'PUF')
            has_errors = post_meta.has_errors

    else:
        # Probably a GET request, load a default form
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        # use puf by default
        use_puf_not_cps = True
        if ('data_source' in params and
                params['data_source'][0] in DATA_SOURCES):
            data_source = params['data_source'][0]
            if data_source != 'PUF':
                use_puf_not_cps = False

        personal_inputs = TaxBrainForm(first_year=start_year,
                                       use_puf_not_cps=use_puf_not_cps)

    init_context = {
        'form': personal_inputs,
        'params': nested_form_parameters(int(start_year), use_puf_not_cps),
        'upstream_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'data_sources': DATA_SOURCES,
        'data_source': data_source,
        'enable_quick_calc': ENABLE_QUICK_CALC
    }

    return render(request, 'taxbrain/input_form.html', init_context)


def resubmit(request, pk):
    """
    This view handles the re-submission of a previously submitted microsim.
    Its primary purpose is to facilitate a mechanism to submit a full microsim
    job after one has submitted parameters for a 'quick calculation'
    """
    # TODO: get this function to work with process_reform
    url = get_object_or_404(TaxBrainRun, pk=pk)

    model = url.inputs
    start_year = model.start_year
    # This will be a new model instance so unset the primary key
    model.pk = None
    # Unset the computed results, set quick_calc to False
    # (this new model instance will be saved in process_model)
    model.job_id = None
    model.jobs_not_ready = None
    model.quick_calc = False
    model.tax_result = None

    log_ip(request)

    # get microsim data
    reform_parameters = json_int_key_encode(
        model.upstream_parameters['reform'])
    assumption_parameters = json_int_key_encode(
        model.upstream_parameters['assumption'])

    user_mods = {'policy': reform_parameters, **assumption_parameters}
    print('data source', model.data_source)
    data = {'user_mods': user_mods,
            'first_budget_year': int(start_year),
            'use_puf_not_cps': model.use_puf_not_cps}

    # start calc job
    years_n = list(range(NUM_BUDGET_YEARS))
    data_list = [dict(year=i, **data) for i in years_n]
    submitted_id, max_q_length = dropq_compute.submit_calculation(
        data_list
    )

    post_meta = PostMeta(
        url=url,
        request=request,
        model=model,
        has_errors=False,
        start_year=start_year,
        data_source=model.data_source,
        do_full_calc=True,
        reform_parameters=reform_parameters,
        assumption_parameters=assumption_parameters,
        reform_inputs_file=(model.inputs_file['reform'] or ""),
        assumption_inputs_file=(model.inputs_file['assumption'] or ""),
        submitted_id=submitted_id,
        max_q_length=max_q_length,
        user=None,
        personal_inputs=None,
        stop_submission=False,
        errors_warnings=None,
        years_n=years_n
    )

    url = save_model(post_meta)

    return redirect(url)


def edit_personal_results(request, pk):
    """
    This view handles the editing of previously entered inputs
    """
    url = get_object_or_404(TaxBrainRun, pk=pk)

    model = url.inputs
    start_year = model.first_year
    model.set_fields()

    msg = ('Field {} has been deprecated. Refer to the Tax-Calculator '
           'documentation for a sensible replacement.')
    form_personal_exemp = TaxBrainForm(
        first_year=start_year,
        use_puf_not_cps=model.use_puf_not_cps,
        instance=model
    )
    form_personal_exemp.is_valid()
    if model.deprecated_fields is not None:
        for dep in model.deprecated_fields:
            form_personal_exemp.add_error(None, msg.format(dep))

    taxcalc_vers_disp = get_version(url, 'upstream_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    init_context = {
        'form': form_personal_exemp,
        'params': nested_form_parameters(int(form_personal_exemp._first_year)),
        'upstream_version': taxcalc_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_years': START_YEARS,
        'start_year': str(form_personal_exemp._first_year),
        'is_edit_page': True,
        'has_errors': False,
        'data_sources': DATA_SOURCES,
        'data_source': model.data_source
    }

    return render(request, 'taxbrain/input_form.html', init_context)
