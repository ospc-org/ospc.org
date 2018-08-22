from ..taxbrain.param_displayers import TaxCalcParam


def default_elasticity_parameters(first_budget_year):
    ''' Create a list of default Elasticity parameters '''
    default_elasticity_params = {}
    default_value = 0.0
    adj_long_name = ("Elasticity of GDP with respect to 1 - average marginal "
                     "tax rate.")
    adj_descr = ("This parameter describes how many percent GDP will change "
                 "for each 1 percent change in 1 - the average "
                 "marginal tax rate, weighted by income, in the "
                 "preceeding year.")

    elasticity_of_gdp = {'value': [default_value], 'col_label': "",
                         'long_name': adj_long_name,
                         'description': adj_descr,
                         'irs_ref': '', 'notes': ''}

    GDP_ELAST_DEFAULT_PARAMS_JSON = {'elastic_gdp': elasticity_of_gdp}

    for k, v in GDP_ELAST_DEFAULT_PARAMS_JSON.items():
        param = TaxCalcParam(k, v, first_budget_year)
        default_elasticity_params[param.nice_id] = param

    return default_elasticity_params
