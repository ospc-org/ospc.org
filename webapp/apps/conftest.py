import pytest
import json
import os
import functools

CUR_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'test_assets'
)


def set_fixture_prop(func):
    """
    Decorator for py.test fixtures that sets a class property if it is called
    by a class. This is required because you cannot pass py.test fixtures as
    arguments for class methods

    py.test fixture in class:
    https://docs.pytest.org/en/latest/unittest.html

    py.test access args for decorated function:
    https://github.com/pytest-dev/pytest/issues/2782
    """
    @functools.wraps(func)
    def wrapper(request):
        res = func(request)
        if request.cls:
            setattr(request.cls, request.fixturename, res)

        return res

    return wrapper

@pytest.fixture()
@set_fixture_prop
def r1(request):
    with open(os.path.join(CUR_PATH, 'r1.json')) as f:
        return f.read()

@pytest.fixture()
def regression_sample_reform():
    with open(os.path.join(CUR_PATH, 'regression_sample_reform.json')) as f:
        return f.read()


@pytest.fixture()
@set_fixture_prop
def bad_reform(request):
    with open(os.path.join(CUR_PATH, 'bad_reform.json')) as f:
        return f.read()


@pytest.fixture()
@set_fixture_prop
def warning_reform(request):
    with open(os.path.join(CUR_PATH, 'warning_reform.json')) as f:
        return f.read()


"""
    ********************************************************************
    The following objects were created for test_param_formatters.py.

    fields_base -- typical metadata associated with TaxBrain runs

    test_coverage_* objects -- these objects do not throw TC warnings or errors
        but include a representative for each type of TC parameter in
        current_law_policy.json

    errors_warnings_* -- these objects do throw warnings and errors and include
        a mostly representative set of TC parameters

    map_back_to_tb -- required for mapping Tax-Calculator styled parameter
        names to TaxBrain styled names

    assumptions_text -- typical assumptions data for TaxBrain runs
    ********************************************************************
"""


@pytest.fixture()
def fields_base():
    _fields_base = {
        '_state': "<django.db.models.base.ModelState object at 0x10c764950>",
        'creation_date': "datetime.datetime(2015, 1, 1, 0, 0)",
        'id': 64,
        'quick_calc': False,
        'first_year': 2017,
    }

    return _fields_base


@pytest.fixture()
@set_fixture_prop
def test_coverage_gui_fields(request):
    _test_coverage_gui_fields = {
        'cpi_offset': ['<', -0.0025],
        'CG_nodiff': [False],
        'FICA_ss_trt': ['<',0.1,'*',0.15,0.2],
        'FICA_mc_trt': ['<',0.1,0.15],
        'STD_0': [8000.0, '*', 10000.0],
        'ID_BenefitSurtax_Switch_0': [True],
        'ID_Charity_c_cpi': True,
        'EITC_rt_2': [1.0],
    }

    return _test_coverage_gui_fields


@pytest.fixture()
@set_fixture_prop
def test_coverage_fields(request):
    # quick work-around to get set_fixture_prop decorator to work with
    # fixture as argument
    # this is equivalent to
    # `test_coverage_fields(fields_base, test_coverage_gui_fields)`
    _fields_base = request.getfixturevalue('fields_base')
    _test_coverage_gui_fields = request.getfixturevalue(
        'test_coverage_gui_fields'
    )
    _test_coverage_fields = dict(_test_coverage_gui_fields, **_fields_base)
    return _test_coverage_fields


@pytest.fixture()
def test_coverage_reform():
    _test_coverage_reform = {
        '_cpi_offset': {'2016': [-0.0025]},
        '_CG_nodiff': {'2017': [False]},
        '_FICA_ss_trt': {'2016': [0.1], '2018': [0.15], '2019': [0.2]},
        '_FICA_mc_trt': {'2016': [0.1], '2017': [0.15]},
        '_STD_single': {'2017': [8000.0], '2019': [10000.0]},
        '_ID_Charity_c_cpi': {'2017': True},
        '_ID_BenefitSurtax_Switch_medical': {'2017': [True]},
        '_EITC_rt_2kids': {'2017': [1.0]}
    }

    return _test_coverage_reform


@pytest.fixture()
def errors_warnings_gui_fields(fields_base):
    _errors_warnings_gui_fields = {
            'STD_0': [7000.0],
            'FICA_ss_trt': [-1.0,'*',0.1],
            'II_brk4_0': [500.0],
            'STD_3': [10000.0, '*', '*', 150.0],
            'ID_BenefitSurtax_Switch_0': [True],
    }

    return _errors_warnings_gui_fields


@pytest.fixture()
def errors_warnings_fields(errors_warnings_gui_fields, fields_base):
    _errors_warnings_fields = dict(errors_warnings_gui_fields, **fields_base)
    return _errors_warnings_fields


@pytest.fixture()
def errors_warnings_reform():
    _errors_warnings_reform = {
        '_STD_single': {'2017': [7000.0]},
        '_FICA_ss_trt': {'2017': [-1.0], '2019': [0.1]},
        '_II_brk4_single': {'2017': [500.0]},
        '_STD_headhousehold': {'2017': [10000.0], '2020': [150.0]},
        '_ID_BenefitSurtax_Switch_medical': {'2017': [True]}
    }

    return _errors_warnings_reform


@pytest.fixture()
def map_back_to_tb():
    with open(os.path.join(CUR_PATH, 'map_back_to_tb.json')) as f:
        return json.loads(f.read())


@pytest.fixture()
def test_coverage_json_reform():
    with open(os.path.join(CUR_PATH, 'test_coverage_json_reform.json')) as f:
        return f.read()


@pytest.fixture()
def errors_warnings_json_reform():
    with open(os.path.join(CUR_PATH, 'errors_warnings_json_reform.json')) as f:
        return f.read()


@pytest.fixture()
def test_coverage_exp_read_json_reform():
    _test_coverage_exp_read_json_reform = {
        2018: {'_ALD_InvInc_ec_base_RyanBrady': [False],
               '_EITC_indiv': [False],
               '_II_no_em_nu18': [False],
               '_CG_nodiff': [False],
               '_ID_Charity_c_cpi': True,
               '_NIIT_PT_taxed': [False],
               '_CTC_new_refund_limited': [False],
               '_ID_BenefitSurtax_Switch': [[True,False,False, False,
                                             False, False, False]],
               '_ID_BenefitCap_Switch': [[False, False, False, False,
                                          False, False, False]],
               '_STD': [[15000.0, 24000.0, 12000.0, 18000.0, 24000.0]],
               '_EITC_rt': [[0.0765, 0.34, 1.0, 0.45]]},
         2020: {'_FICA_ss_trt': [0.2]},
         2019: {'_FICA_ss_trt': [0.1]}
    }

    return _test_coverage_exp_read_json_reform


@pytest.fixture()
def errors_warnings_exp_read_json_reform():
    _errors_warnings_exp_read_json_reform = {
        2018: {
            '_FICA_ss_trt': [-1.0],
            '_ID_BenefitSurtax_Switch': [[True, True, True, True,
                                          True, True, False]],
            '_STD': [[10000.0, 24000.0, 12000.0, 20000.0, 24000.0]]
        },
        2019: {
            '_FICA_ss_trt': [0.1],
            '_II_brk4': [[500.0, 321268.5, 160634.25, 160634.25, 321268.5]]
        },
        2020: {
            '_STD': [[10409.1, 24981.84, 12490.92, 150.0, 24981.84]]
        }
    }
    return _errors_warnings_exp_read_json_reform


@pytest.fixture()
def errors():
    with open(os.path.join(CUR_PATH, 'policy_errors.txt')) as f:
        return f.read()


@pytest.fixture()
def warnings():
    with open(os.path.join(CUR_PATH, 'policy_warnings.txt')) as f:
        return f.read()


@pytest.fixture()
def warnings_behavior():
    with open(os.path.join(CUR_PATH, 'behavior_warnings.txt')) as f:
        return f.read()


@pytest.fixture()
def errors_behavior():
    with open(os.path.join(CUR_PATH, 'behavior_errors.txt')) as f:
        return f.read()


@pytest.fixture()
def errors_warnings(warnings, errors):
    return {'warnings': warnings, 'errors': errors}


@pytest.fixture()
def errors_warnings_policy_behavior(errors, warnings, warnings_behavior,
                                    errors_behavior):
    return {
        'policy':{
            'errors': errors,
            'warnings': warnings
        },
        'behavior': {
            'errors': errors_behavior,
            'warnings': warnings_behavior
        }
    }


def policy_errors_warnings(errors_warnings, empty_errors_warnings):
    return {'policy': errors_warnings, 'behavior': empty_errors_warnings}


@pytest.fixture()
def empty_errors_warnings():
    return {'errors': {}, 'warnings': {}}


@pytest.fixture()
def empty_errors_warnings_policy_behavior(empty_errors_warnings):
    return {'policy': empty_errors_warnings, 'behavior': empty_errors_warnings}


@pytest.fixture()
def exp_errors_warnings():
    with open(os.path.join(CUR_PATH, 'exp_errors_warnings_policy.json')) as f:
        return json.loads(f.read())

@pytest.fixture()
def exp_errors_warnings_policy_behavior():
    with open(os.path.join(CUR_PATH,
                           'exp_errors_warnings_policy_behavior.json')) as f:
        return json.loads(f.read())


@pytest.fixture()
@set_fixture_prop
def assumptions_text(request):
    with open(os.path.join(CUR_PATH, 'assumptions_text.txt')) as f:
        return f.read()


@pytest.fixture()
def exp_assumptions_text():
    _exp_assumptions_text = {
        'growdiff_response': {},
        'consumption': {},
        'behavior': {
            2018: {
                '_BE_sub': [1.0],
                 '_BE_inc': [-0.6],
                 '_BE_cg': [-0.67]}
            },
        'growdiff_baseline': {}
    }

    return _exp_assumptions_text


@pytest.fixture()
@set_fixture_prop
def test_coverage_behavioral_gui_fields(request):
    _test_coverage_behavoiral_gui_fields = {
        'BE_sub': [1.0],
        'BE_inc': [-0.6],
        'BE_cg': [-0.67]
    }
    return _test_coverage_behavoiral_gui_fields


@pytest.fixture()
@set_fixture_prop
def test_coverage_behavioral_fields(request):
    # quick work-around to get set_fixture_prop decorator to work with
    # fixture as argument
    # this is equivalent to
    # `test_coverage_fields(fields_base, test_coverage_behavioral_gui_fields)`
    _fields_base = request.getfixturevalue('fields_base')
    _fields_base.pop('quick_calc', None)
    _test_coverage_behavoiral_gui_fields = request.getfixturevalue(
        'test_coverage_behavioral_gui_fields'
    )
    _test_coverage_behavoiral_fields = dict(
        _test_coverage_behavoiral_gui_fields,
        **_fields_base
    )
    return _test_coverage_behavoiral_fields


@pytest.fixture()
def no_assumptions_text():
    with open(os.path.join(CUR_PATH, 'no_assumptions_text.txt')) as f:
        return f.read()


@pytest.fixture()
def no_assumptions_text_json(no_assumptions_text):
    return json.loads(no_assumptions_text)


@pytest.fixture()
def errors_warnings_json_assumptions():
    with open(os.path.join(CUR_PATH, 'errors_warnings_json_assumptions.json')) as f:
        return f.read()


@pytest.fixture()
def errors_warnings_exp_read_json_assumptions():
    _ew_assumptions = {
        'consumption': {},
        'behavior': {
            2018: {'_BE_sub': [-0.8], '_BE_inc': [0.6]}},
        'growdiff_baseline': {},
        'growdiff_response': {}
    }

    return _ew_assumptions

@pytest.fixture()
@set_fixture_prop
def skelaton_res_lt_0130(request):
    _path = os.path.join(CUR_PATH, "skelaton_res_lt_0130.json")
    with open(_path) as js:
        return json.loads(js.read())


@pytest.fixture()
@set_fixture_prop
def skelaton_res_gt_0130(request):
    _path = os.path.join(CUR_PATH, "skelaton_res_gt_0130.json")
    with open(_path) as js:
        return json.loads(js.read())
