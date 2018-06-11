import os

from django.utils.safestring import mark_safe
import taxcalc

from django.conf import settings

DISTRIBUTION_TOOLTIP = "Key variables in the computation of tax liabilities."
DIFFERENCE_TOOLTIP = "Key variables that highlight the differences between two tax plans."
PAYROLL_TOOLTIP = " Include employee and employer payroll taxes in output."
INCOME_TOOLTIP = "Include individual income taxes in output."
BASE_TOOLTIP = "Current law as defined by default parameters."
REFORM_TOOLTIP = "The reform proposal as defined by user-provided parameters."
INCOME_BINS_TOOLTIP = "Tax units are binned according to the income group to which they belong."
INCOME_DECILES_TOOLTIP = " Tax units are binned according to the income decile to which they belong."
FISCAL_CURRENT_LAW = "Fiscal Current Law"
FISCAL_REFORM = "Fiscal Reform tooltip"
FISCAL_CHANGE = "Fiscal Change tooltip"
METR_TOOLTIP = "Marginal effective tax rate on new investments. The METR includes the impact of the first level of taxation on the incentives to invest."
METTR_TOOLTIP = "Marginal effective total tax rate on new investments. The METTR includes the impact of all levels of taxation (both on business entities and savers) on the incentives to invest."
COC_TOOLTIP = "The cost of capital is calculated as the net-of-depreciation, before-tax rate of return."
DPRC_TOOLTIP = "Net present value of depreciation deductions."

START_YEARS = ('2013', '2014', '2015', '2016', '2017', '2018')
START_YEAR = os.environ.get('START_YEAR', '2017')
DATA_SOURCES = ('PUF', 'CPS')
DEFAULT_SOURCE = os.environ.get('DEFAULT_SOURCE', 'PUF')

TAXCALC_VERS_RESULTS_BACKWARDS_INCOMPATIBLE = "0.13.0"

OUT_OF_RANGE_ERROR_MSG = mark_safe("""
<div align="left">
    Some fields have warnings or errors. Fields with warnings have message(s)
    below them beginning with \'WARNING\', and fields with errors have
    message(s) below them beginning with \'ERROR\'.
    <br /> <br />
    &emsp;- If the field has a warning message , then review the input to make sure
    it is correct and click \'SUBMIT\' to run the model with these inputs.
    <br />
    &emsp;- If the field has an error message, then the parameter value must be
    changed so that it is in a valid range.
</div>""")

WEBAPP_VERSION = settings.WEBAPP_VERSION

tcversion_info = taxcalc._version.get_versions()

TAXCALC_VERSION = tcversion_info['version']
