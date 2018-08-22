import datetime
from django.utils import timezone
from urllib.parse import urlparse, parse_qs
import os

import taxcalc


from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User

from ..constants import START_YEAR, START_YEARS

from .forms import has_field_errors, DynamicElasticityInputsModelForm
from .models import TaxBrainElastRun
from ..taxbrain.models import TaxBrainRun
from ..taxbrain.views import dropq_compute
from ..taxbrain.helpers import json_int_key_encode
from ..core.views import CoreRunDetailView, CoreRunDownloadView
from ..core.models import Tag, TagOption

from ..taxbrain.submit_data import JOB_PROC_TIME_IN_SECONDS

from .helpers import default_elasticity_parameters

from ..formatters import get_version

tcversion_info = taxcalc._version.get_versions()
TAXCALC_VERSION = tcversion_info['version']

WEBAPP_VERSION = settings.WEBAPP_VERSION

NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))


class TaxBrainElastRunDetailView(CoreRunDetailView):
    model = TaxBrainElastRun

    result_header = "Elastic Results"

    tags = []
    aggr_tags = [
        Tag(key="default",
            values=[
                TagOption(
                    value="gdp_elast",
                    title=""),
            ])]

    def has_link_to_dyn(self):
        return False


class TaxBrainElastRunDownloadView(CoreRunDownloadView):
    model = TaxBrainElastRun


def dynamic_elasticities(request, pk):
    """
    This view handles the dynamic macro elasticities input page and
    calls the function that handles the calculation on the inputs.
    """
    start_year = START_YEAR
    if request.method == 'POST':
        # Client is attempting to send inputs, validate as form data
        fields = dict(dict(request.POST), **dict(request.GET))
        fields = {k: v[0] if isinstance(v, list) else v
                  for k, v in list(fields.items())}
        start_year = fields.get('start_year', START_YEAR)
        elast_gdp = fields.get('elastic_gdp')
        print(fields, start_year, elast_gdp)
        # TODO: migrate first_year to start_year to get rid of weird stuff like
        # this
        fields['first_year'] = fields['start_year']
        # use_puf_not_cps set to True by default--doesn't matter for dynamic
        # input page. It is there for API consistency
        dyn_mod_form = DynamicElasticityInputsModelForm(start_year, True,
                                                        fields)
        print(str(dyn_mod_form.errors))
        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            gdp_elasticity = float(model.elastic_gdp)

            # get microsim data
            outputsurl = TaxBrainRun.objects.get(pk=pk)
            model.micro_run = outputsurl
            taxbrain_model = outputsurl.inputs
            model.data_source = taxbrain_model.data_source
            # get taxbrain data
            # necessary for simulations before PR 641
            reform_parameters = json_int_key_encode(
                taxbrain_model.upstream_parameters['reform'])
            # empty assumptions dictionary
            assumptions_dict = {"behavior": {},
                                "growdiff_response": {},
                                "consumption": {},
                                "growdiff_baseline": {},
                                "growmodel": {}}

            user_mods = dict({'policy': reform_parameters}, **assumptions_dict)
            data = {'user_mods': user_mods,
                    'gdp_elasticity': gdp_elasticity,
                    'start_year': int(start_year),
                    'use_puf_not_cps': model.use_puf_not_cps}
            print(data)
            # raise ValueError()
            # start calc job
            data_list = [dict(year_n=i, **data)
                         for i in range(NUM_BUDGET_YEARS)]
            submitted_id, max_q_length = (
                dropq_compute.submit_elastic_calculation(data_list))

            if not submitted_id:
                form_personal_exemp = dyn_mod_form
            else:
                model.first_year = int(start_year)
                model.save()

                unique_url = TaxBrainElastRun()
                if request.user.is_authenticated():
                    current_user = User.objects.get(pk=request.user.id)
                    unique_url.user = current_user

                if unique_url.upstream_vers is not None:
                    pass
                else:
                    unique_url.upstream_vers = TAXCALC_VERSION

                if unique_url.webapp_vers is not None:
                    pass
                else:
                    unique_url.webapp_vers = WEBAPP_VERSION

                unique_url.inputs = model
                unique_url.job_id = submitted_id

                cur_dt = timezone.now()
                future_offset = datetime.timedelta(
                    seconds=((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS))
                expected_completion = cur_dt + future_offset
                unique_url.exp_comp_datetime = expected_completion
                unique_url.save()
                return redirect(unique_url)

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:
        # Probably a GET request, load a default form
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        form_personal_exemp = DynamicElasticityInputsModelForm(
            first_year=start_year,
            use_puf_not_cps=True
        )

    elasticity_default_params = default_elasticity_parameters(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': elasticity_default_params,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_year': start_year,
        'pk': pk
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/elasticity.html', init_context)


def edit_dynamic_elastic(request, pk):
    """
    This view handles the editing of previously compute elasticity of GDP
    dynamic simulation
    """
    url = get_object_or_404(TaxBrainElastRun, pk=pk)

    model = url.inputs
    start_year = model.first_year

    form_personal_exemp = DynamicElasticityInputsModelForm(
        first_year=start_year,
        use_puf_not_cps=model.use_puf_not_cps,
        instance=model
    )
    elasticity_default_params = default_elasticity_parameters(int(start_year))

    taxcalc_vers_disp = get_version(url, 'upstream_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    init_context = {
        'form': form_personal_exemp,
        'params': elasticity_default_params,
        'taxcalc_version': taxcalc_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_year': str(start_year),
        'pk': model.micro_run.pk
    }

    return render(request, 'dynamic/elasticity.html', init_context)


def dynamic_landing(request, pk):
    """
    This view gives a landing page to choose a type of dynamic simulation that
    is linked to the microsim
    """
    outputsurl = get_object_or_404(TaxBrainRun, pk=pk)
    include_ogusa = True
    init_context = {
        'pk': pk,
        'is_authenticated': request.user.is_authenticated(),
        'include_ogusa': include_ogusa,
        'start_year': outputsurl.inputs.start_year,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION
    }

    return render(request, 'dynamic/landing.html', init_context)
