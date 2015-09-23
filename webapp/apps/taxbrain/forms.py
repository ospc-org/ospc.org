from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from .models import TaxSaveInputs
from .helpers import TaxCalcField, TaxCalcParam, TAXCALC_DEFAULT_PARAMS


class PersonalExemptionForm(ModelForm):

    class Meta:
        model = TaxSaveInputs
        exclude = ['creation_date']
        widgets = {}
        labels = {}

        for param in TAXCALC_DEFAULT_PARAMS.values():
            for field in param.col_fields:
                attrs = {
                    'class': 'form-control',
                    'placeholder': field.default_value,
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                widgets[field.id] = forms.TextInput(attrs=attrs)
                labels[field.id] = field.label

            if param.inflatable:
                field = param.cpi_field
                attrs = {
                    'class': 'form-control sr-only',
                    'placeholder': "{0}".format(field.default_value),
                }

                if param.coming_soon:
                    attrs['disabled'] = True

                widgets[field.id] = forms.NullBooleanSelect(attrs=attrs)

        # Keeping label text, may want to use some of these custom labels
        # instead of those specified in params.json
        """
        labels = {
            'FICA_trt': _('Combined FICA rate'),
            'SS_Income_c': _('Max Taxable Earnings'),
            'SS_percentage1': _('Rate 1'),
            'SS_thd50_0': _('Single'),
            'SS_thd50_1': _('Married filing Jointly'),
            'SS_thd50_2': _('Head of Household'),
            'SS_thd50_3': _('Married filing Separately'),
            'SS_percentage2': _('Rate 2'),
            'SS_thd85_0': _('Single'),
            'SS_thd85_1': _('Married filing Jointly'),
            'SS_thd85_2': _('Head of Household'),
            'SS_thd85_3': _('Married filing Separately'),

            'AMED_trt': _('Threshold'),
            'AMED_thd_0': _('Single'),
            'AMED_thd_1': _('Married filing Jointly'),
            'AMED_thd_2': _('Head of Household'),
            'AMED_thd_3': _('Married filing Separately'),

            'ALD_StudentLoan_HC': _('Student Loan Interest Deduction'),
            'ALD_SelfEmploymentTax_HC': _('Deduction Half of Self-Employment Tax'),
            'ALD_SelfEmp_HealthIns_HC': _('Self Employed Health Insurance Deduction'),
            'ALD_KEOGH_SEP_HC': _('Payment to KEOGH Plan and SEP Deduction'),
            'ALD_EarlyWithdraw_HC': _('Forfeited Int. Penalty - Early Withdrawal of Savings'),
            'ALD_Alimony_HC': _('Alimony Paid'),
            'FEI_ec_c': _('Foreign earned income exclusion'),

            'II_em': _('Amount'),
            'II_prt': _('Phaseout'),
            'II_em_ps_0': _('Single'),
            'II_em_ps_1': _('Married filing Jointly'),
            'II_em_ps_2': _('Head of Household'),
            'II_em_ps_3': _('Married filing Separately'),

            'STD_0': _('Single'),
            'STD_1': _('Married filing Jointly'),
            'STD_2': _('Head of Household'),
            'STD_3': _('Married filing Separately'),
            'STD_Aged_0': _('Single'),
            'STD_Aged_1': _('Married filing Jointly'),
            'STD_Aged_2': _('Head of Household'),
            'STD_Aged_3': _('Married filing Separately'),

            'ID_medical_frt': _('Floor as a % of Income'),
            'ID_Casualty_frt': _('Floor as a % of Income'),
            'ID_Miscellaneous_frt': _('Floor as a % of Income'),
            'ID_Charity_crt_Cash': _('Ceiling for cash as % of AGI'),
            'ID_Charity_crt_Asset': _('Ceiling for assets as % of AGI'),
            'ID_ps_0': _('Single'),
            'ID_ps_1': _('Married filing Jointly'),
            'ID_ps_2': _('Head of Household'),
            'ID_ps_3': _('Married filing Separately'),
            'ID_prt': _('Phaseout Rate'),
            'ID_crt': _('Max Percent Forfeited'),

            'CG_rt1': _('Rate 1'),
            'CG_thd1_0': _('Single'),
            'CG_thd1_1': _('Married filing Jointly'),
            'CG_thd1_2': _('Head of Household'),
            'CG_thd1_3': _('Married filing Separately'),
            'CG_rt2': _('Rate 2'),
            'CG_thd2_0': _('Single'),
            'CG_thd2_1': _('Married filing Jointly'),
            'CG_thd2_2': _('Head of Household'),
            'CG_thd2_3': _('Married filing Separately'),
            'CG_rt3': _('Rate 3'),
            'Dividend_rt1': _('Rate 1'),
            'Dividend_thd1_0': _('Single'),
            'Dividend_thd1_1': _('Married filing Jointly'),
            'Dividend_thd1_2': _('Head of Household'),
            'Dividend_thd1_3': _('Married filing Separately'),
            'Dividend_rt2': _('Rate 2'),
            'Dividend_thd2_0': _('Single'),
            'Dividend_thd2_1': _('Married filing Jointly'),
            'Dividend_thd2_2': _('Head of Household'),
            'Dividend_thd2_3': _('Married filing Separately'),
            'Dividend_rt3': _('Rate 3'),
            'Dividend_thd3_0': _('Single'),
            'Dividend_thd3_1': _('Married filing Jointly'),
            'Dividend_thd3_2': _('Head of Household'),
            'Dividend_thd3_3': _('Married filing Separately'),
            
            'NIIT_trt': _('Rate'),
            'NIIT_thd_0': _('Single'),
            'NIIT_thd_1': _('Married filing Jointly'),
            'NIIT_thd_2': _('Head of Household'),
            'NIIT_thd_3': _('Married filing Separately'),
            'II_rt1': _('Rate 1'),
            'II_brk1_0': _('Single'),
            'II_brk1_1': _('Married filing Jointly'),
            'II_brk1_2': _('Head of Household'),
            'II_brk1_3': _('Married filing Separately'),
            'II_rt2': _('Rate 2'),
            'II_brk2_0': _('Single'),
            'II_brk2_1': _('Married filing Jointly'),
            'II_brk2_2': _('Head of Household'),
            'II_brk2_3': _('Married filing Separately'),
            'II_rt3': _('Rate 3'),
            'II_brk3_0': _('Single'),
            'II_brk3_1': _('Married filing Jointly'),
            'II_brk3_2': _('Head of Household'),
            'II_brk3_3': _('Married filing Separately'),
            'II_rt4': _('Rate 4'),
            'II_brk4_0': _('Single'),
            'II_brk4_1': _('Married filing Jointly'),
            'II_brk4_2': _('Head of Household'),
            'II_brk4_3': _('Married filing Separately'),
            'II_rt5': _('Rate 5'),
            'II_brk5_0': _('Single'),
            'II_brk5_1': _('Married filing Jointly'),
            'II_brk5_2': _('Head of Household'),
            'II_brk5_3': _('Married filing Separately'),
            'II_rt6': _('Rate 6'),
            'II_brk6_0': _('Single'),
            'II_brk6_1': _('Married filing Jointly'),
            'II_brk6_2': _('Head of Household'),
            'II_brk6_3': _('Married filing Separately'),
            'II_rt7': _('Rate 7'),

            'AMT_em_0': _('Single'),
            'AMT_em_1': _('Married filing Jointly'),
            'AMT_em_2': _('Head of Household'),
            'AMT_em_3': _('Married filing Separately'),
            'AMT_prt': _('Phaseout Rate'),
            'AMT_em_ps_0': _('Single'),
            'AMT_em_ps_1': _('Married filing Jointly'),
            'AMT_em_ps_2': _('Head of Household'),
            'AMT_em_ps_3': _('Married filing Separately'),
            'AMT_trt1': _('AMT rate'),
            'AMT_trt2': _('Surtax rate'),
            'AMT_tthd': _('Surtax Threshold'),
            
            'EITC_rt_0': _('0 Kids'),
            'EITC_rt_1': _('1 Kid'),
            'EITC_rt_2': _('2 Kids'),
            'EITC_rt_3': _('3+ Kids'),
            'EITC_prt_0': _('0 Kids'),
            'EITC_prt_1': _('1 Kid'),
            'EITC_prt_2': _('2 Kids'),
            'EITC_prt_3': _('3+ Kids'),
            'EITC_ps_0': _('0 Kids'),
            'EITC_ps_1': _('1 Kid'),
            'EITC_ps_2': _('2 Kids'),
            'EITC_ps_3': _('3+ Kids'),
            'EITC_c_0': _('0 Kids'),
            'EITC_c_1': _('1 Kid'),
            'EITC_c_2': _('2 Kids'),
            'EITC_c_3': _('3+ Kids'),
            'CTC_c': _('Max Credit'),
            'CTC_prt': _('Phaseout Rate'),
            'CTC_ps_0': _('Single'),
            'CTC_ps_1': _('Married filing Jointly'),
            'CTC_ps_2': _('Head of Household'),
            'CTC_ps_3': _('Married filing Separately'),
            'ACTC_rt': _('Rate'),
            'ACTC_ChildNum': _('Qualifying # of children'),
        }
        """

def has_field_errors(form):
    """
    This allows us to see if we have field_errors, as opposed to only having
    form.non_field_errors. I would prefer to put this in a template tag, but
    getting that working with a conditional statement in a template was very
    challenging.
    """
    if not form.errors:
        return False

    for field in form:
        if field.errors:
            return True

    return False
