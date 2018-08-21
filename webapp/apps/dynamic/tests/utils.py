# os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list,
                                 package_up_vars, format_csv,
                                 arrange_totals_by_row, default_taxcalc_data)

from ...test_assets.utils import get_dropq_compute_from_module

START_YEAR = '2016'


def do_dynamic_sim(client, base_name, microsim_response, pe_reform,
                   start_year=START_YEAR):
    # Link to dynamic simulation
    idx = microsim_response.url[:-1].rfind('/')
    model_num = microsim_response.url[idx + 1:-1]
    dynamic_landing = '/dynamic/{1}/?start_year={2}'.format(
        base_name, model_num, start_year)
    response = client.get(dynamic_landing)
    assert response.status_code == 200

    # Go to behavioral input page
    dynamic_behavior = '/dynamic/{0}/{1}/?start_year={2}'.format(
        base_name, model_num, start_year)
    response = client.get(dynamic_behavior)
    assert response.status_code == 200

    # Do the partial equilibrium job submission
    response = client.post(dynamic_behavior, pe_reform)
    assert response.status_code == 302
    print(response)

    # The results page will now succeed
    next_response = client.get(response.url)
    reload_count = 0
    while reload_count < 2:
        if next_response.status_code == 200:
            break
        elif next_response.status_code == 302:
            next_response = client.get(next_response.url)
            reload_count = 0
        else:
            raise RuntimeError("unable to load results page")
    assert "results/" in response.url
    return response
