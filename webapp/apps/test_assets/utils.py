import json
from ..taxbrain.compute import MockCompute
from django.core.files.uploadedfile import SimpleUploadedFile

def do_micro_sim(client, reform):
    '''do the proper sequence of HTTP calls to run a microsim'''
    #Monkey patch to mock out running of compute jobs
    import sys
    from webapp.apps.taxbrain import views
    webapp_views = sys.modules['webapp.apps.taxbrain.views']
    webapp_views.dropq_compute = MockCompute()
    from webapp.apps.dynamic import views
    dynamic_views = sys.modules['webapp.apps.dynamic.views']
    dynamic_views.dropq_compute = MockCompute(num_times_to_wait=1)

    response = client.post('/taxbrain/', reform)
    # Check that redirect happens
    assert response.status_code == 302
    idx = response.url[:-1].rfind('/')
    assert response.url[:idx].endswith("taxbrain")
    return response


def do_micro_sim_from_file(client, start_year, reform_text, assumptions_text=None):
    # Monkey patch to mock out running of compute jobs
    import sys
    from webapp.apps.taxbrain import views
    webapp_views = sys.modules['webapp.apps.taxbrain.views']
    webapp_views.dropq_compute = MockCompute()

    tc_file = SimpleUploadedFile("test_reform.json", reform_text)
    data = {u'docfile': tc_file,
            u'has_errors': [u'False'],
            u'start_year': start_year, 'csrfmiddlewaretoken':'abc123'}

    if assumptions_text:
        tc_file2 = SimpleUploadedFile("test_assumptions.json",
                                      assumptions_text)
        data['assumpfile'] = tc_file2

    response = client.post('/taxbrain/file/', data)
    # Check that redirect happens
    assert response.status_code == 302
    return response


def check_posted_params(mock_compute, params_to_check, start_year):
    """
    Make sure posted params match expected results
    user_mods: parameters that are actually passed to taxcalc
    params_to_check: gives truth value for parameters that we want to check
                     (formatted as taxcalc dict style reform)
    """
    last_posted = mock_compute.last_posted
    user_mods = json.loads(last_posted["user_mods"])
    assert last_posted["first_budget_year"] == start_year
    for year in params_to_check:
        for param in params_to_check[year]:
            assert user_mods[str(year)][param] == params_to_check[year][param]


def get_post_data(start_year, _ID_BenefitSurtax_Switches=True, quick_calc=False):
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
