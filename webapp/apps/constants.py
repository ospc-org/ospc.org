import os

DIAGNOSTIC_TOOLTIP = "Key variables in the computation of tax liabilities."
DIFFERENCE_TOOLTIP = "Key variables that highlight the differences between two tax plans."
PAYROLL_TOOLTIP = " Include employee and employer payroll taxes in output."
INCOME_TOOLTIP = "Include individual income taxes in output."
BASE_TOOLTIP = "Current law as defined by default parameters."
REFORM_TOOLTIP = "The reform proposal as defined by user-provided parameters."
EXPANDED_TOOLTIP = "The tab variable includes adjusted gross income, non-taxable interest income, taxable investment income excluded from AGI, non-taxable social security benefits, the employer’s share of FICA, and above the line adjustments to AGI on form 1040."
ADJUSTED_TOOLTIP = "Not yet available."
INCOME_BINS_TOOLTIP = "Tax units are binned according to the income group to which they belong."
INCOME_DECILES_TOOLTIP = " Tax units are binned according to the income decile to which they belong."
FISCAL_CURRENT_LAW = "Fiscal Current Law"
FISCAL_REFORM = "Fiscal Reform tooltip"
FISCAL_CHANGE = "Fiscal Change tooltip"
METR_TOOLTIP = "Marginal effective tax rate on new investments. The METR includes the impact of the first level of taxation on the incentives to invest."
METTR_TOOLTIP = "Marginal effective total tax rate on new investments. The METTR includes the impact of all levels of taxation (both on business entities and savers) on the incentives to invest."
COC_TOOLTIP = "The cost of capital is calculated as the net-of-depreciation, before-tax rate of return."
DPRC_TOOLTIP = "Net present value of depreciation deductions."

START_YEARS = ('2013', '2014', '2015', '2016', '2017')
START_YEAR = os.environ.get('START_YEAR', '2017')
