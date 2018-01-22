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

    return wrapper

@pytest.fixture()
@set_fixture_prop
def r1(request):
    with open(os.path.join(CUR_PATH, 'r1.json')) as f:
        return f.read()

@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def fields_base():
    _fields_base = {
        '_state': "<django.db.models.base.ModelState object at 0x10c764950>",
        'creation_date': "datetime.datetime(2015, 1, 1, 0, 0)",
        'id': 64,
        'quick_calc': False,
        'first_year': 2017,
    }

    return _fields_base


@pytest.fixture(scope="session")
def test_coverage_fields(fields_base):
    _test_coverage_fields = dict(
        cpi_offset = ['<', -0.0025],
        CG_nodiff = [False],
        FICA_ss_trt = ['<',0.1,'*',0.15,0.2],
        FICA_mc_trt = ['<',0.1,0.15],
        STD_0 = [8000.0, '*', 10000.0],
        ID_BenefitSurtax_Switch_0 = [True],
        ID_Charity_c_cpi = True,
        EITC_rt_2 = [1.0],
        **fields_base
    )

    return _test_coverage_fields


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def errors_warnings_fields(fields_base):
    _errors_warnings_fields = dict(
            STD_0 = [7000.0],
            FICA_ss_trt = [-1.0,'*',0.1],
            II_brk4_0 = [500.0],
            STD_3= [10000.0, '*', '*', 150.0],
            ID_BenefitSurtax_Switch_0= [True],
            **fields_base
    )

    return _errors_warnings_fields


@pytest.fixture(scope="session")
def errors_warnings_reform():
    _errors_warnings_reform = {
        u'_STD_single': {u'2017': [7000.0]},
        u'_FICA_ss_trt': {u'2017': [-1.0], u'2019': [0.1]},
        u'_II_brk4_single': {u'2017': [500.0]},
        u'_STD_headhousehold': {u'2017': [10000.0], u'2020': [150.0]},
        u'_ID_BenefitSurtax_Switch_medical': {u'2017': [True]}
    }

    return _errors_warnings_reform


@pytest.fixture(scope="session")
def map_back_to_tb():
    with open(os.path.join(CUR_PATH, 'map_back_to_tb.json')) as f:
        return json.loads(f.read())


@pytest.fixture(scope="session")
def test_coverage_json_reform():
    with open(os.path.join(CUR_PATH, 'test_coverage_json_reform.json')) as f:
        return f.read()


@pytest.fixture(scope="session")
def errors_warnings_json_reform():
    with open(os.path.join(CUR_PATH, 'errors_warnings_json_reform.json')) as f:
        return f.read()


@pytest.fixture(scope="session")
def test_coverage_exp_read_json_reform():
    _test_coverage_exp_read_json_reform = {
        2017: {u'_EITC_rt': [[0.0765, 0.34, 1.0, 0.45]],
               u'_NIIT_PT_taxed': [False],
               u'_ID_BenefitCap_Switch': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
               u'_ALD_InvInc_ec_base_RyanBrady': [False],
               u'_EITC_indiv': [False],
               u'_ID_BenefitSurtax_Switch': [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]],
               u'_STD': [[10000.0, 12700.0, 6350.0, 9350.0, 12700.0]],
               u'_II_no_em_nu18': [False],
               u'_ID_Charity_c_cpi': True,
               u'_CG_nodiff': [False],
               u'_CTC_new_refund_limited': [False]},
        2018: {u'_FICA_ss_trt': [0.1]},
        2020: {u'_FICA_ss_trt': [0.2]}
    }

    return _test_coverage_exp_read_json_reform


@pytest.fixture(scope="session")
def errors_warnings_exp_read_json_reform():
    _errors_warnings_exp_read_json_reform = {
        2017:
            {u'_II_brk4': [[500.0, 233350.0, 116675.0, 212500.0, 233350.0]],
            u'_STD': [[7000.0, 12700.0, 6350.0, 10000.0, 12700.0]],
            u'_ID_BenefitSurtax_Switch': [[True, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]],
            u'_FICA_ss_trt': [-1.0]},
        2019: {u'_FICA_ss_trt': [0.1]},
        2020: {u'_STD': [[7486.87, 13583.32, 6791.67, 150.0, 13583.32]]}
    }

    return _errors_warnings_exp_read_json_reform


@pytest.fixture(scope="session")
def errors():
    with open(os.path.join(CUR_PATH, 'errors.txt')) as f:
        return f.read()


@pytest.fixture(scope="session")
def warnings():
    with open(os.path.join(CUR_PATH, 'warnings.txt')) as f:
        return f.read()


@pytest.fixture(scope="session")
def errors_warnings(warnings, errors):
    return {'warnings': warnings, 'errors': errors}


@pytest.fixture(scope="session")
def empty_errors_warnings():
    return {'errors': {}, 'warnings': {}}

@pytest.fixture(scope="session")
def exp_errors_warnings():
    with open(os.path.join(CUR_PATH, 'exp_errors_warnings.json')) as f:
        return json.loads(f.read())


@pytest.fixture()
@set_fixture_prop
def assumptions_text(request):
    with open(os.path.join(CUR_PATH, 'assumptions_text.txt')) as f:
        return f.read()


@pytest.fixture(scope="session")
def exp_assumptions_text():
    _exp_assumptions_text = {
        'growdiff_response': {},
        'consumption': {},
        'behavior': {
            2017: {u'_BE_sub': [1.0], u'_BE_inc': [-0.6], u'_BE_cg': [-0.67]}},
        'growdiff_baseline': {}
    }

    return _exp_assumptions_text


@pytest.fixture(scope="session")
def no_assumptions_text():
    with open(os.path.join(CUR_PATH, 'no_assumptions_text.txt')) as f:
        return f.read()


@pytest.fixture(scope="session")
def no_assumptions_text_json(no_assumptions_text):
    return json.loads(no_assumptions_text)
