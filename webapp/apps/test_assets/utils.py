import json
import os
import sys

from ..taxbrain.compute import MockCompute

from ..taxbrain.models import OutputUrl
from ..taxbrain.forms import PersonalExemptionForm

from ..dynamic import views
from ..taxbrain import views

from django.core.files.uploadedfile import SimpleUploadedFile

NUM_BUDGET_YEARS = int(os.environ.get("NUM_BUDGET_YEARS", "10"))

def get_dropq_compute_from_module(module_import_path, attr='dropq_compute',
                                  MockComputeObj=MockCompute, **mc_args):
    """
    mocks dropq compute object from specified module

    returns: mocked dropq compute object
    """
    module_views = sys.modules[module_import_path]
    setattr(module_views, attr, MockComputeObj(**mc_args))
    return getattr(module_views, attr)

def do_micro_sim(client, data, tb_dropq_compute=None, dyn_dropq_compute=None,
                 compute_count=None, post_url='/taxbrain/'):
    """
    do the proper sequence of HTTP calls to run a microsim
    tb_dropq_compute: mocked taxbrain dropq_compute object; set to default
                      config if None
    dyn_dropq_compute: mocked dynamic dropq_compute object; set to default
                       config if None
    compute_count: number of jobs submitted; only checked in quick_calc tests
    post_url: url to post data; is also set to /taxbrain/file/ for file_input
              tests

    returns: response object, taxbrain mock dropq compute object,
             dynamic dropq compute object, primary key for model run
    """
    #Monkey patch to mock out running of compute jobs
    if tb_dropq_compute is None:
        tb_dropq_compute = get_dropq_compute_from_module(
            'webapp.apps.taxbrain.views',
            num_times_to_wait=0
        )
    if dyn_dropq_compute is None:
        dyn_dropq_compute = get_dropq_compute_from_module(
            'webapp.apps.dynamic.views',
            num_times_to_wait=1
        )

    response = client.post(post_url, data)
    # Check that redirect happens
    assert response.status_code == 302
    idx = response.url[:-1].rfind('/')
    assert response.url[:idx].endswith("taxbrain")

    # Check for good response
    response2 = client.get(response.url)
    # TODO: check compute count once NUM_BUDGET_YEARS env variable issue is
    # resolved
    assert response2.status_code == 200
    if compute_count is not None:
        assert tb_dropq_compute.count == compute_count
    # return response
    return {"response": response,
            "tb_dropq_compute": tb_dropq_compute,
            "dyn_dropq_compute": dyn_dropq_compute,
            "pk": response.url[idx+1:-1]}


def check_posted_params(mock_compute, params_to_check, start_year):
    """
    Make sure posted params match expected results
    user_mods: parameters that are actually passed to taxcalc
    params_to_check: gives truth value for parameters that we want to check
                     (formatted as taxcalc dict style reform)
    """
    last_posted = mock_compute.last_posted
    user_mods = json.loads(last_posted["user_mods"])
    assert last_posted["first_budget_year"] == int(start_year)
    for year in params_to_check:
        for param in params_to_check[year]:
            act = user_mods["policy"][str(year)][param]
            exp = params_to_check[year][param]
            assert exp == act


def get_post_data(start_year, _ID_BenefitSurtax_Switches=True, quick_calc=False):
    """
    Convenience function for posting GUI data
    """
    data = {u'has_errors': [u'False'],
            u'start_year': unicode(start_year),
            'csrfmiddlewaretoken':'abc123'}
    if _ID_BenefitSurtax_Switches:
        switches = {u'ID_BenefitSurtax_Switch_0': [u'True'],
                    u'ID_BenefitSurtax_Switch_1': [u'True'],
                    u'ID_BenefitSurtax_Switch_2': [u'True'],
                    u'ID_BenefitSurtax_Switch_3': [u'True'],
                    u'ID_BenefitSurtax_Switch_4': [u'True'],
                    u'ID_BenefitSurtax_Switch_5': [u'True'],
                    u'ID_BenefitSurtax_Switch_6': [u'True']}
        data.update(switches)
    if quick_calc:
        data['quick_calc'] = 'Quick Calculation!'
    return data


def get_file_post_data(start_year, reform_text, assumptions_text=None, quick_calc=False):
    """
    Convenience function for posting file input data
    """
    tc_file = SimpleUploadedFile("test_reform.json", reform_text)
    data = {u'docfile': tc_file,
            u'has_errors': [u'False'],
            u'start_year': unicode(start_year),
            u'quick_calc': quick_calc,
            'csrfmiddlewaretoken':'abc123'}

    if assumptions_text is not None:
        tc_file2 = SimpleUploadedFile("test_assumptions.json",
                                      assumptions_text)
        data['assumpfile'] = tc_file2

    return data


def get_taxbrain_model(fields, first_year=2017,
                       quick_calc=False, taxcalc_vers="0.13.0",
                       webapp_vers="1.2.0", exp_comp_datetime = "2017-10-10",
                       Form=PersonalExemptionForm, UrlModel=OutputUrl):
    fields = fields.copy()
    del fields['_state']
    del fields['creation_date']
    del fields['id']
    for key in fields:
        if isinstance(fields[key], list):
            fields[key] = ','.join(map(str, fields[key]))

    personal_inputs = Form(first_year, fields)

    model = personal_inputs.save()
    model.job_ids = ['1','2','3']
    model.json_text = None
    model.first_year = first_year
    model.quick_calc = quick_calc
    model.save()

    unique_url = UrlModel()
    unique_url.taxcalc_vers = taxcalc_vers
    unique_url.webapp_vers = webapp_vers
    unique_url.unique_inputs = model
    unique_url.model_pk = model.pk
    unique_url.exp_comp_datetime = exp_comp_datetime
    unique_url.save()

    return unique_url
